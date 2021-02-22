FROM s53ostlund/openta-base:v312
#RUN apt-get update \
#    && apt-get install -y \
#    graphviz \
#    libcairo2 \
#    libcairo2-dev \
#    libgraphviz-dev \
#    libjpeg-dev \
#    libxml2-dev \
#    libxslt1-dev \
#    libzmq3-dev
#
#COPY django/requirements.txt /srv/openta/django/requirements.txt
WORKDIR /srv/openta/django
#RUN pip install -r requirements.txt
#RUN pip install gunicorn==19.9.0
#RUN pip uninstall --yes psycopg2
#RUN pip install psycopg2-binary==2.7.7
#RUN mkdir /srv/multicourse
COPY multicourse/ /srv/multicourse
COPY . /srv/openta
#COPY ./multicourse  /srv/multicourse
EXPOSE 8000
