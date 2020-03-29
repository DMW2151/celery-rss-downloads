import os
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.environ.get('MONGO_DB')
app.config['MONGO_URI'] = f"""mongodb://{os.environ.get('MONGO_USER', '')}:{os.environ.get('MONGO_USER_PW', '')}@rss_backend_1:27017/{os.environ.get('MONGO_DB', '')}"""

mongo = PyMongo(app)

@app.route('/feeds', methods=['POST'])
def add_feed():
    '''
    Docs - Add Feed
    '''
    feeds = mongo.db.feeds
    #os.environ.get('MONGO_DB', '')]

    rss_url = request.json['url']
    feed_name = request.json['src']
    
    try:
        feed_id = feeds.insert(
            {'url' : rss_url, 'src' : feed_name}
        )
    
        # Confirm entry
        new_obj = feeds.find_one({'_id' : feed_id})

        return jsonify({
                'result': {
                    'url' : new_obj['url'], 
                    'src' : new_obj['src']
                }
            }
        )

    except Exception as exc: #Handle this better...
        return jsonify({'result': 'Failed'})
        

if __name__ == '__main__':
    app.run(host='0.0.0.0')
