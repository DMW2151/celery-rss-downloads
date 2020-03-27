from __future__ import absolute_import, unicode_literals

from celery import Celery
from celery.execute import send_task
from celery.schedules import crontab
from kombu import Queue
import os

BROKER_URL = os.environ.get('MONGO_BROKER_URL', 
    'mongodb://rss_backend_1:27017/jobs')
    
BACKEND_URL = os.environ.get('MONGO_BACKEND_URL', 
    'mongodb://rss_backend_1:27017/backend')

app = Celery('proj',
	broker=BROKER_URL, 
    backend=BACKEND_URL,
	include=['proj.tasks']
)
app.conf.task_default_queue = 'default'

app.conf.update(
	task_serializer='json',
	accept_content=['json'],  # Ignore other content
	result_serializer='json',
	timezone='US/Eastern',
	enable_utc=True,    
)

app.conf.task_routes = {'proj.tasks.download_response': {'queue': 'downloads'}}

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    
    # Check Feeds Every 1 mins - Update Sets
    sender.add_periodic_task(
        60.0, call_update_episode_stash.s(),
    )

    # Download Every 1 mins - Update Sets 
    #  NOTE: OFFSET THIS SO `call_update_episode_stash` and 
    # `call_get_new_episodes` run back to back - or chain them...
    sender.add_periodic_task(
        60.0, call_get_new_episodes.s(),
    )

@app.task
def call_update_episode_stash():
    '''Wrapper task, interface for proj.tasks.update_episode_stash'''
    send_task('proj.tasks.update_episode_stash')

@app.task
def call_get_new_episodes():
    '''Wrapper task, interface for proj.tasks.get_new_episodes'''
    send_task('proj.tasks.get_new_episodes')
    
if __name__ == '__main__':
	app.start()
