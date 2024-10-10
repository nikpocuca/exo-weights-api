FROM redis:7.0-rc AS red 

ENV DEBIAN_FRONTEND=noninteractive

COPY redis.conf /usr/local/etc/redis/redis.conf

RUN mkdir -p /home/app_user/app
