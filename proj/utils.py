import os
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests
from lxml.etree import QName
from pymongo import MongoClient
from datetime import datetime

def parse_rss_feed(feed_data):
    '''
    Parse RSS Feed and return list of dicts (documents) for Mongo
    args:
        feed_data: dict:
            url: str: target RSS feed
            src: str: optional title
    returns:
        outp: list[dict]: All .//channel/item attribute from XML as 
        list of dictionary
    '''
    
    r = requests.get(feed_data.get('url'))
    try: 
        r.raise_for_status()
    except requests.exceptions.HTTPError as e: 
        pass

    root = ET.fromstring(r.content)
    
    if not feed_data.get('src'):
        # Search for title of feed if not passed by user - If fails...then None
        feed_title_elem = root.find('.//channel/title') 
        feed_title = feed_title_elem.text if feed_title_elem is not None else None
    else:
        feed_title = feed_data.get('src')

    outp = []
    for obj in root.findall('.//channel/item'):
        
        d = {'src': feed_title}
        for elem in list(obj):
            if not elem.text:
                alt_value = elem.get('url') or elem.get('href')                
                d[QName(elem.tag).localname] = alt_value
            else: # link DNE; assign text as value
                d[QName(elem.tag).localname] = elem.text
        outp.append(d)

    return outp

class MongoDBConnection(object):
    """
    Create connection with MongoDB as contextmanager, from: <STACK OVERFLOW URL>
    args:
        connection_params: dict: corresponds to Mongo auth. 
            Contains: host, username, password, authSource (i.e. dbname)
        db_name: str: db to connect to
    returns:
        pymongo.Database: db_connection
    """

    def __init__(self, params=None):
        if not params: # NOTE: Default Connection for Now...
            params = {
                'host': 'backend',
                'username': os.environ.get('MONGO_WORKER'),
                'password': os.environ.get('MONGO_WORKER_PW'),
                'authSource': os.environ.get('MONGO_DB')
            }
        self.params = params
        self.connection = None

    def __enter__(self):
        self.connection = MongoClient(**self.params)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

