FROM openta-base:latest
RUN yes | apt-get install nginx gettext-base
RUN rm -f /etc/nginx/sites-enabled/default
#RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx.conf /etc/nginx/conf.d/default.template

RUN chgrp -R 0 \
  /etc/nginx/conf.d/ \
  /var/cache/ \
  /var/run \
  /var/log/nginx
#
RUN chmod -R g=u \
  /etc/nginx/conf.d/ \
  /var/cache/ \
  /var/run \
  /var/log/nginx

RUN chmod -R o+w \
  /etc/nginx/conf.d/ \
  /var/cache/ \
  /var/run \
  /var/log/nginx

RUN sed -i.bak 's/^user/#user/' /etc/nginx/nginx.conf

#RUN addgroup nginx root
#
#USER nginx
