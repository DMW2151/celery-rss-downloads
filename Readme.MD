# Celery w. MongoDB Broker/Backend - RSS Monitoring Sandbox

## Description

Project runs a Celery on an Raspberry Pi 3 queue to run scheduled downloads of files posted to RSS feeds.

Uses MongoDB as a message broker for Celery. Choose Mongo b/c it's (arguably) the only broker that can do double-duty and act as a suitable db.

Uses Flask to interface with MongoDB so I can post requests to some local url to register feeds. 


## Use

Start services - Mongo, Celery, Flask....

```bash
> docker-compose up --build
```

### MongoDB

Copy in Mongo DB authorization scripts & run setup script (`db_user_setup.sh`). Allows auth from other container w. identical credentials. Where <BACKEND_ALIAS> is the container alias or image ID.

```bash
docker cp ./mongo/db_user_setup.sh <BACKEND_ALIAS>:/db_user_setup.sh
docker exec -ti <BACKEND_ALIAS> bash /db_user_setup.sh
```

### Celery Worker

Exec into <WORKER_ALIAS> and start Celery Beat. Default configuration of this project (`./proj/celery_cfg.py`) queries `feeds` collection and updates `episodes` every 10 min, downloads files every 5 min.

```bash
> docker exec -ti <WORKER_ALIAS> bash -c 'celery -A proj beat --app=proj.celery_cfg'
```

### Host

Flask exposes several (WIP) routes to the host machine to help manage downloads.

```bash
# Post to `feeds`; Add a feed to download; POST -X 127.0.0.1:2151/feeds ...
> curl -X POST 127.0.0.1:2151/feeds -d '{"url": "https://rss.art19.com/techmeme-ridehome", "title": "TechMeme"}' -H "Content-Type: application/json"
```

### TODO OR Done

* 03-29-2020 ❏ - Make ~~Django~~ Flask work. No need to have one big Django app here. With that said, need to add routes to Flask that make this useable.

* 03-27-2020 ✅ - Updates to Downloads:

    * Since we're just making HTTP requests we should move to a gevent execution pool w. a ton of threads. [Great article](https://www.distributedpython.com/2018/10/26/celery-execution-pool/)

    * If count of queued downloads > concurrency, then Celery beat has no thread to use to check for new feeds or update the to download queue. Create two queues, one for downloading audio (long-running), one for all other tasks. [Great article w. examples](https://hackernoon.com/using-celery-with-multiple-queues-retries-and-scheduled-tasks-589fe9a4f9ba). 

* 03-26-2020 ✅- Some websites don't quite appreciate 100s of HTTP requests from at a time. Add retry and delay params.



### Appendix - Configuring RPi3 (Optional)

No requirement for this project to run on RPi3, the Mongo image referenced in `./docker-compose.yml` (`andresvidal/rpi3-mongodb3`) could be replaced with `mongo::latest` for a 64-bit system. The 32-bit system enforces some limitations on MongoDB...

#### Mounting Drive

Followed tutorial [here](https://www.pidramble.com/wiki/benchmarks/external-usb-drives) to partition portion of removable storage to ext4. 
