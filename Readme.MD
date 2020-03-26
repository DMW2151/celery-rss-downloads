# Celery w. MongoDB Broker/Backend - RSS Monitoring Sandbox

## Description
Run Celery to manage downloads of files posted to some RSS feeds, use MongoDB as a message broker and a backend for posting target URLs.

## Usage
```bash
## Start Services - Mongo + Celery
$ docker-compose up --build
```

Start beat...
```bash
$ celery -A proj beat --app=proj.celery_cfg
```

## TODO

* 03-25-2020 - Add option to alias files on download and download episodes to subdirectories by feed. For example, save the file below with `./audio/NPR/NPR_News_03_25_2020_11PM_ET.mp3` instead of `./audio/newscast230803.mp3`. 

```python
import proj.tasks as t

target_url = 'https://play.podtrac.com/npr-500005/edge1.pod.npr.org/anon.npr-mp3/npr/newscasts/2020/03/25/newscast230803.mp3'
t.download_response(url=target_url, alias='NPR News: 03-25-2020 11PM ET')
```

