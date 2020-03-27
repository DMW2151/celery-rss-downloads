FROM python:3.7.4  
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

COPY ./proj ./proj

RUN CFLAGS=-O0 pip3 install --no-cache-dir -r ./proj/requirements.txt  

#Comment out to Debug, run single node in container w: 
ENTRYPOINT ["celery", "-A", "proj",  "worker", "-l", "info", "--app=proj.celery_cfg", "-Q=default,downloads", "--pool=gevent", "--concurrency=10"]

