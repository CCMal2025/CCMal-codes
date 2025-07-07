FROM python:3.11-slim-bullseye

WORKDIR /usr/src/app

RUN apt-get update \
    && apt-get install -y git libxml2 libjansson4 libyaml-0-2 vim build-essential

COPY resource resource

# install redis
WORKDIR /usr/src/app/resource

RUN tar -xzf redis-7.4.3.tar.gz && \
    cd redis-7.4.3 && \
    make && \
    make install && \
    cd .. && \
    rm -rf redis-7.4.3

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /usr/src/app/redis-dir && redis-server --daemonize yes --port 24779 --dir /usr/src/app/redis-dir && python3 initialization.py

RUN chmod +x entrypoint.sh
EXPOSE 8000

CMD ["/usr/src/app/entrypoint.sh"]