FROM python:3.5
MAINTAINER Henrik Gustafsson

# Simple development environment for OpenTA

# Use with
# docker run --rm -p 127.0.0.1:8000:8000 -v $(pwd):/openta -i -t openta
# to sync with workind directory outside container, or simply
# docker run --rm -p 127.0.0.1:8000:8000 -i -t openta


# -- Preliminaries

# Recommended method for installing nodejs with package manager on Debian (minus sudo)
RUN (curl -sL https://deb.nodesource.com/setup_6.x | bash -) && apt-get install -y \
    graphviz \
    libcairo2 \
    libcairo2-dev \
    libgraphviz-dev \
    libjpeg-dev \
    libxml2-dev \
    libxslt1-dev \
    libzmq3-dev \
    nodejs \
    tmux \
    lsyncd

RUN npm install -g brunch

COPY django/requirements.txt /tmp/openta/django/requirements.txt
COPY frontend/package.json /tmp/openta/frontend/package.json

WORKDIR /tmp/openta/django
RUN pip install -r requirements.txt

WORKDIR /tmp/openta/frontend
RUN npm install


# --

COPY . /openta

# merge folders
RUN rsync -au /openta /tmp/

# config for folder sync
RUN echo "sync { default.rsync, delay = 0, source = '/openta', target = '/tmp/openta', delete = 'running' }" > /etc/lsyncd

WORKDIR /tmp/openta

# start django (backend), brunch (frontend watcher) and lsyncd (file sync with mounted volume)
CMD tmux \
    new-session 'cd django/backend && python manage.py runserver 0.0.0.0:8000' \; \
    split-window -d -p 25 'cd frontend && brunch watch' \; \
    split-window -d -p 25 'lsyncd -nodaemon /etc/lsyncd'  \; attach 

EXPOSE 8000

