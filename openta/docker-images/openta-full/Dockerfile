FROM opentaproject/openta-base:multi
WORKDIR /srv
COPY ./srv /srv
WORKDIR /srv/openta/django/backend
COPY  povray.conf  povray.ini  requirements.txt  server.py  .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt install -y at 
RUN apt install -y pandoc 
RUN apt update 
RUN apt install -y libegl1
EXPOSE 8000
