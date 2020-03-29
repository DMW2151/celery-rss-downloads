# Celery w. MongoDB Broker/Backend - RSS Monitoring Sandbox

## Description
Project runs a Celery on an Raspberry Pi 3 queue to manage downloads of files posted to RSS feeds.

Uses MongoDB as a message broker and a database for posting target URLs + search on episode descriptions/content etc. Uses Django to interface with MongoDB so I can post requests to some local url to register feeds instead of authing into MongoDB to add a new RSS feed. Choose Mongo b/c it's (arguably) the only broker that's a suitable db in it's own right.


## Configuring RPi3 (Optional)
No requirement for this project to run on RPi3, the Mongo image referenced in `./docker-compose.yml` (`andresvidal/rpi3-mongodb3`) could be replaced with `mongo::latest` for a 64-bit system.

### Notes on RPi3 Setup (for future self)

Mount a drive to store media, where "PARTITION" (e.g. `sda1`) is selected from the result of `fdisk -l` and "PATH/TO/MOUNT" is the mount name (e.g. `/MediaES`). 

Followed tutorial (here)[https://www.pidramble.com/wiki/benchmarks/external-usb-drives] to partition portion of removable storage to ext4. 

```bash
$ sudo fdisk /dev/<PARTITION>

#Enter the following options when prompted: n, p, 1, <enter>, <enter>, w
#Format the partition

$ sudo mkfs -t ext4 /dev/<PARTITION>

$ sudo chown -R pi:pi </PATH/TO/MOUNT>
# Create a directory to use as the filesystem mount: (e.g. sudo mkdir /ssd)
$ sudo mount /dev/<PARTITION> </PATH/TO/MOUNT>
```

## Useage 

Start services - Mongo + Celery, `--build` flag only required if changes made to Celery worker container. This excludes contents of `./proj` (e.g. all tasks + utils) since they're synced into the container w. a volume. 

```bash
$ docker-compose up --build
```

Copy in Mongo DB authorization scripts and run setup script (db_user_setup.sh), allows auth from other container w. identical credentials

```bash
docker cp ./mongo/db_user_setup.sh rss_backend_1:/db_user_setup.sh
docker exec -ti rss_backend_1 bash /db_user_setup.sh
```

Exec into rss_master_node_1 and start Celery Beat, Beat is Celery's scheduler. Default configuration of this project (`./proj/celery_cfg.py`) asks for 

```bash
$ docker exec -ti rss_master_node_1 bash -c 'celery -A proj beat --app=proj.celery_cfg'
```

Manual interaction w. DB...this should be removed soon...
```bash
docker exec -ti rss_backend_1 mongo <DB> 

> db.feeds.insert({'url': 'https://www.espn.com/espnradio/feeds/rss/podcast.xml/_/id/25869711'})
```

Flask...
```
curl -X POST 127.0.0.1:5000/feeds -d '{"url": "https://www.espn.com/espnradio/feeds/rss/podcast.xml/_/id/9941853", "title": "TechMeme"}' -H "Content-Type: application/json"
```

## TODO OR Done

* 03-29-2020 - Make ~~Django~~ Flask Work...No Need to use Django.

* 03-28-2020 ✅ - When feed is registed in `db.feeds`, the default is to download all files in the feed. This is rude. Set param s.t. only episodes from the last month are downloaded on feeds by default. 

* 03-27-2020 ✅ - Noticed downloads were not particuarly quick. Since we're just making HTTP requests we should move to a gevent execution pool w. a ton of threads. (Great article)[https://www.distributedpython.com/2018/10/26/celery-execution-pool/]

* 03-26-2020 ✅ - If count of queued downloads > concurrency, then Celery beat has no thread to use to check for new feeds or update the to download queue. Create two queues, one for downloading audio (long-running), one for all other tasks. (Great article w. examples)[https://hackernoon.com/using-celery-with-multiple-queues-retries-and-scheduled-tasks-589fe9a4f9ba]. **Solution**: configure routing in `celery_cfg.py` (see below) and add `"-Q=default,downloads"` to `ENTRYPOINT`

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

