#!bin/bash
echo """
// For Worker
db.createUser({
    user: '$MONGO_WORKER' , 
    pwd: '$MONGO_WORKER_PW', 
    roles: [
        { role: 'readWrite', db:'$MONGO_DB'}
    ]})

// For Flask
db.createUser({
    user: '$MONGO_USER' , 
    pwd: '$MONGO_USER_PW', 
    roles: [
        { role: 'readWrite', db:'$MONGO_DB'}
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
mongo ${MONGO_DB} user_create.js 