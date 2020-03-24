FROM python:3.7.4  
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

COPY ./proj ./proj

RUN pip3 install --no-cache-dir -r ./proj/requirements.txt  

# Run Beat
RUN celery multi start w1 -A proj -l debug --app=proj.celery_cfg
RUN celery -A proj worker -l info --app=proj.celery_cfg 

