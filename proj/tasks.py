from __future__ import absolute_import, unicode_literals

import os
import shutil

import requests
from celery import group, chain, subtask
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger
import  time
import datetime

import re
import proj.utils as utils
from proj.celery_cfg import app
import pymongo
from bson.objectid import ObjectId
from dateutil.parser import parse as date_parse

logger = get_task_logger(__name__)

# DB Interaction Tasks
@app.task
def get_feeds(connection_params=None):
    '''
    Query Mongo and dump active feeds Collection
    '''
    c = utils.MongoDBConnection()
    db_name = os.environ.get('MONGO_DB')
    with c:
        db = c.connection[db_name]
        feeds = db.feeds
        valid_feeds = feeds.find(
                {'url' : { '$exists' : True } },
                {'url': 1, '_id': 0, 'src': 1}
        )
    
    return [{'url': obj.get('url'), 'src': obj.get('src', '')} for obj in valid_feeds]

@app.task
def insert_feed(feed_data, connection_params=None):
    '''
    Add feed to Mongo Collection
    args:
        feed_data: dict: new source/feed to register
        connection_params: dict: corresponds to Mongo auth. 
            Contains: host, username, password, authSource (i.e. dbname)
        db_name: str: db to connect to
    retuns:
        N/A
    Note: In this Collection URL is UNIQUE: 
        db.feeds.createIndex(
            {url:1},
            {unique:true}
        )
    '''
    c = utils.MongoDBConnection()
    db_name = os.environ.get('MONGO_DB')
    with c:
        db = c.connection[db_name]
        feeds = db.feeds
        try:
            _id = feeds.insert_one(feed_data).inserted_id
            return _id     
        except pymongo.errors.DuplicateKeyError: #Ignore Dupl entries 
            pass

@app.task
def get_recent_episodes(connection_params=None, delta_days=30):
    '''
    Query Mongo and get record of episodes recently added to the episodes collection
    args:
        connection_params: dict: corresponds to Mongo auth. 
            Contains: host, username, password, authSource (i.e. dbname)
        db_name: str: db to connect to
        delta_min: int: NOTE: Ideally here we will check 
            all episodes "since last execution of `call_update_episode_stash.s()`"
    returns:
        list[dict]: list of dict containg target urls + alias
    '''
    
    def parse_src_entry(d):
        '''Parse RSS Feed Entry - Assumes Uniformity of Labels'''
        pod_title = re.sub('[^0-9a-zA-Z]+', '_', d.get('title', ''))

        return {
            'url': d.get('enclosure'),
            'alias': pod_title, 
            'src': d.get('src', 'misc')
        }

    # Query Episodes ingested in last N-Minutes by using ObjectID date property - See NOTE in Docstring...
    # Also...could use `$setOnInsert: { dateAdded: new Date() }` to avoid this arithmatic :(
    
    pub_date_lwr_bnd = (datetime.datetime.now() - datetime.timedelta(days=delta_days))

    c = utils.MongoDBConnection()
    db_name = os.environ.get('MONGO_DB')
    with c:
        db = c.connection[db_name]
        episodes = db.episodes
        
        recent_episodes = episodes.find(
                {"enclosure" : { '$exists' : True },
                "pubDate" : { '$gte' : pub_date_lwr_bnd }},
                {"_id": 0, "title": 1, "enclosure": 1, "src": 1}
        )
    
    return [parse_src_entry(obj) for obj in recent_episodes]

@app.task(ignore_result=True)
def insert_episodes_data(feed_data, connection_params=None):
    '''
    Add Episodes to Mongo Collection
    args:
        feed_data:dict:
            url: str: path to RSS feed public address
            title: str: feed name
        connection_params: dict: corresponds to Mongo auth. 
            Contains: host, username, password, authSource (i.e. dbname)
        db_name: str: db to connect to
    returns:
        list[str]: ids of inserted objects
    Note: In this Collection Enclosure is UNIQUE: 
        db.episodes.createIndex(
            {enclosure:1},
            {unique:true}
        )
    '''
    f = utils.parse_rss_feed(feed_data)
    ids = []

    c = utils.MongoDBConnection()
    db_name = os.environ.get('MONGO_DB')
    with c:
        db = c.connection[db_name]
        episodes = db.episodes

        # Single insert performance > batch insert, almost all feeds 
        # fail batch insert on dupl key error and fall back to single inserts
        for ep in f:
            try:
                # Handle Date, yuck...fix
                ep['pubDate'] = date_parse(ep.get('pubDate', str(datetime.datetime.now())))
                _id = episodes.insert_one(ep).inserted_id
                ids.append(_id)
            except pymongo.errors.DuplicateKeyError: #Ignore Dupl
                pass
    return ids
    
# Download Tasks
@app.task(bind=True, ignore_result=True)
def download_response(self, episode_data):
    '''
    Download target file, only function that matters...
    args:
        episode_data:
            url: str: download target's URL
            alias: str: download target's local filename
            data_dir: str: download target's local directory (feed name)
    '''
    url, alias, src = episode_data.get('url', ''), episode_data.get('alias'), episode_data.get('src')
    
    data_dir = os.path.join('/rss_library', src)
    local_filename = os.path.join(
            data_dir,
            alias if alias is not None else url.split('/')[-1]
    )
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    try:
        if not os.path.exists(local_filename):
            with requests.get(url, stream=True) as r:
                with open(local_filename, 'wb') as f:
                   shutil.copyfileobj(r.raw, f)

    except Exception as exc:
        raise exc
        # overrides the default delay && retry after 1 minute
        raise self.retry(exc=exc, countdown=60, max_retries=3)

# Master Scheduled Tasks
@app.task
def dmap(it, callback):
    '''
    Map a callback over an iterator and return as a group
    args:
        it: list/tuple/gen: input iterator
        callback: celery.Task: function to apply for each item in it
    return:
        celery.group: ...
    '''
    callback = subtask(callback)
    return group(callback.clone([arg,]) for arg in it)()

@app.task(ignore_result=True)
def update_episode_stash():
    '''
    Wrapper Task: Combines querying feeds collection and pushing new 
    episodes to episodes collection
    '''
    process_list = (get_feeds.s() | dmap.s(insert_episodes_data.s()))
    process_list.apply_async()

@app.task(ignore_result=True)
def get_new_episodes():
    '''
    Wrapper Task: Combines querying episodes and downloading to disk
    '''
    process_list = (get_recent_episodes.s() | dmap.s(download_response.s()))
    process_list.apply_async()


