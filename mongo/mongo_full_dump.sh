!#/bin/bash

dest  = `date +%m%d%y`
mongodump -d ${MONGO_DB} -h 127.0.0.1 --out=/dump/$dest
