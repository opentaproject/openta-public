FROM python:3.11.9-bullseye
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg >/dev/null
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ bullseye-pgdg main"  > /etc/apt/sources.list.d/postgresql.list'
RUN apt upgrade -y
RUN apt update -y \
    && apt-get --fix-broken install -y \
    graphviz \
    libldap2-dev \
    libcairo2 \
    libcairo2-dev \
    libgraphviz-dev \
    libjpeg-dev \
    libxml2-dev \
    libxslt1-dev \
    libzmq3-dev \
    memcached  \
    libmemcached-dev  \
    vim \
    postgresql-14\
    rsync \
    apt-utils \
    redis \
    libnss3 \
    poppler-utils \
    uuid \
    bc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    povray \
    povray-includes
RUN apt-get install --yes --no-install-recommends ca-certificates curl gpg 
RUN apt-get update -y  \
    && apt-get install -y \
    cron\
    at \
    libegl1\
    pandoc;
COPY requirements-openta.txt /srv/openta/django/requirements.txt
WORKDIR /srv/openta/django
RUN pip install --upgrade pip
RUN pip install -q  supervisor gunicorn pypdf
#RUN pip install -r requirements.txt
#RUN pip install --upgrade django_ragamuffin twilio redis

RUN apt-get update -y \
	&& apt-get install -y \
	pgbouncer
RUN apt-get update && apt-get install -y netcat-openbsd;
