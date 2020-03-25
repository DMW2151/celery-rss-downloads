#!bin/bash
echo """
db.createUser({
    user: '$MONGO_USER' , 
    pwd: '$MONGO_USER_PW', 
    roles: [
        { role: 'readWrite', db:'$MONGO_AUTH_SRC_DB'}
    ]})

db.feeds.createIndex(
        {url:1},
        {unique:true}
)

db.episodes.createIndex(
        {enclosure:1},
        {unique:true}
)
""" > user_create.js

# Execute user_create.js on DB from root role
mongo audio user_create.js 