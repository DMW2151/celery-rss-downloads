import os
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests
from lxml.etree import QName
from pymongo import MongoClient

def parse_rss_feed(url):
    '''
    Parse RSS Feed and return list of dicts (documents) for Mongo
    args:
        url: str: target RSS feed
    returns:
        outp: list[dict]: All .//channel/item attribute from XML as 
        list of dictionary
    '''
    r = requests.get(url)
    try: 
        r.raise_for_status()
    except requests.exceptions.HTTPError as e: 
        pass # Handle: Log this

    root = ET.fromstring(r.content)
    outp = []
    for obj in root.findall('.//channel/item'):
        d = dict()
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
    Create connection with MongoDB as contextmanager
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
                'host': 'db',
                'username': os.environ.get('MONGO_USER'),
                'password': os.environ.get('MONGO_USER_PW'),
                'authSource': os.environ.get('MONGO_AUTH_SRC_DB')
            }
        self.params = params
        self.connection = None

    def __enter__(self):
        self.connection = MongoClient(**self.params)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


# def mongo_connection(connection_params=None):
#     '''Doc'''
#     if not connection_params:
#         # NOTE: Default Connection for Now...
#         connection_params = {
#             'host': 'db',
#             'username': os.environ.get('MONGO_USER'),
#             'password': os.environ.get('MONGO_USER_PW'),
#             'authSource': os.environ.get('MONGO_AUTH_SRC_DB')
#         }

#         client = MongoDBConnection(connection_params)
                
#     return client
