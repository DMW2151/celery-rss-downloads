FROM python:3.7.4  
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

COPY ./proj ./proj

RUN CFLAGS=-O0 pip3 install --no-cache-dir -r ./proj/requirements.txt  

RUN mkdir var/log/celery /var/run/celery

ENTRYPOINT ["celery", "-A", "proj",  "worker", "-l", "warn", "--app=proj.celery_cfg", "--queues=default,downloads", "--pool=gevent", "--concurrency=50", "--pidfile=/var/run/celery/%n.pid", "--logfile=/var/log/celery/%n%I.log"]

