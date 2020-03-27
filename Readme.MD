# Celery w. MongoDB Broker/Backend - RSS Monitoring Sandbox

## Description
Run Celery to manage downloads of files posted to some RSS feeds, use MongoDB as a message broker and a backend for posting target URLs.

## Usage

## Prelim

mount volume to rpi
```bash
sudo mkdir /media/easystore &&\
sudo chown -R pi:pi /media/easystore &&\
sudo mount /dev/sdb2 /media/easystore -o uid=pi,gid=pi
```

## Use

Start Services - Mongo + Celery

```bash
$ docker-compose up --build
```

Copy in Mongo DB Auth Scripts...just to save from customizing a new dockerfile on top of mongo-rpi image
run setup script (db_user_setup.sh), allows auth from other container w. identical credentials

```bash
cd ~/RSS && docker cp ./mongo/db_user_setup.sh rss_backend_1:/db_user_setup.sh
docker exec -ti rss_backend_1 bash /db_user_setup.sh
```

Exec into rss_master_node_1 and start celery beat
```bash
$ docker exec -ti rss_master_node_1 bash -c 'celery -A proj beat --app=proj.celery_cfg'
```

```bash
docker exec -ti rss_backend_1 mongo audio

> db.feeds.insert({'url': 'https://www.espn.com/espnradio/feeds/rss/podcast.xml/_/id/25869711'})
```



## TODO

* 03-25-2020 - Add option to alias files on download and download episodes to subdirectories by feed. For example, save the file below with `./audio/NPR/NPR_News_03_25_2020_11PM_ET.mp3` instead of `./audio/newscast230803.mp3`. 

```python
import proj.tasks as t

target_url = 'https://play.podtrac.com/npr-500005/edge1.pod.npr.org/anon.npr-mp3/npr/newscasts/2020/03/25/newscast230803.mp3'
t.download_response(url=target_url, alias='NPR News: 03-25-2020 11PM ET')
```

