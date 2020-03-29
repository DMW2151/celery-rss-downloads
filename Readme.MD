# Celery w. MongoDB Broker/Backend - RSS Monitoring Sandbox

## Description

Project runs a Celery on an Raspberry Pi 3 queue to manage downloads of files posted to RSS feeds.

Uses MongoDB as a message broker and a database for posting target URLs + search on episode descriptions/content etc. Uses Flask to interface with MongoDB so I can post requests to some local url to register feeds instead of authing into MongoDB to add a new RSS feed. Choose Mongo b/c it's (arguably) the only broker that's a suitable db in it's own right.

## Configuring RPi3 (Optional)

### Volume

No requirement for this project to run on RPi3, the Mongo image referenced in `./docker-compose.yml` (`andresvidal/rpi3-mongodb3`) could be replaced with `mongo::latest` for a 64-bit system. The 32-bit system enforces some limitations on MongoDB...

### Mounting Drive

Mount a drive to storage media, where "PARTITION" (e.g. `sda1`) is selected from the result of `fdisk -l` and "PATH/TO/MOUNT" is the mount name (e.g. `/MediaES`). 

Followed tutorial [here](https://www.pidramble.com/wiki/benchmarks/external-usb-drives) to partition portion of removable storage to ext4. 

```bash
> sudo fdisk /dev/<PARTITION>

#Enter the following options when prompted: n, p, 1, <enter>, <enter>, w
#Format the partition

> sudo mkfs -t ext4 /dev/<PARTITION>

> sudo chown -R pi:pi </PATH/TO/MOUNT>
# Create a directory to use as the filesystem mount: (e.g. sudo mkdir /ssd)
> sudo mount /dev/<PARTITION> </PATH/TO/MOUNT>
```

## Use

Start services - Mongo, Celery, Flask. The `--build` flag only required if changes made to Celery worker container. This excludes contents of `./proj` (e.g. all tasks + utils) since they're synced into the container w. a volume.

```bash
> docker-compose up --build
```

### MongoDB

Copy in Mongo DB authorization scripts and run setup script (db_user_setup.sh), allows auth from other container w. identical credentials. Where <BACKEND_ALIAS> is the container alias or image ID.

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

* 03-28-2020 ✅ - When feed is registed in `db.feeds`, the default is to download all files in the feed. This is rude. Set param s.t. only episodes from the last month are downloaded on feeds by default. 

* 03-27-2020 ✅ - Noticed downloads were not particuarly quick. Since we're just making HTTP requests we should move to a gevent execution pool w. a ton of threads. [Great article](https://www.distributedpython.com/2018/10/26/celery-execution-pool/)

* 03-26-2020 ✅ - If count of queued downloads > concurrency, then Celery beat has no thread to use to check for new feeds or update the to download queue. Create two queues, one for downloading audio (long-running), one for all other tasks. [Great article w. examples](https://hackernoon.com/using-celery-with-multiple-queues-retries-and-scheduled-tasks-589fe9a4f9ba). **Solution**: configure routing in `celery_cfg.py` (see below) and add `"-Q=default,downloads"` to `ENTRYPOINT`

```python
app.conf.task_routes = {'proj.tasks.download_response': {'queue': 'downloads'}}
```

* 03-26-2020 ✅- Some websites don't quite appreciate 100s of HTTP requests from me at a time. Add retry and delay params to `download_response`.

* 03-25-2020 ✅ - Add option to alias files on download and download episodes to subdirectories by feed. For example, save the file below with `./audio/NPR/NPR_News_03_25_2020_11PM_ET.mp3` instead of `./audio/newscast230803.mp3`. 

```python
import proj.tasks as t

target_url = 'https://play.podtrac.com/npr-500005/edge1.pod.npr.org/anon.npr-mp3/npr/newscasts/2020/03/25/newscast230803.mp3'
t.download_response(url=target_url, alias='NPR News: 03-25-2020 11PM ET')
```
