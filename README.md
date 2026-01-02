
# OpenTA web platform

This repository makes available the OpenTA web platform intended for engineering and science courses at the University level. It has been used for many years at Chalmers and Gothenburg University.  

Documentation is available on "https://opentaproject.com".

## Installation using Docker

This initial release documents how to get the platform installed on a private Unix server. The easiest method is using Docker. OpenTA together all the goodies such as povray, mathplot, latex is big package, so make sure you have 8Gb available. Alternatively, get a vps to avoid cluttering your own machine.

## Installing on remote vps

You can install on your local unix machine and use localhost. Another option is to 
install on a vps in the cloud where you can login  as *USER@REMOTE* to avoid cluttering
your own machine with docker images. Then use the command

```ssh -q -L 8000:localhost:8000  USER@REMOTE```

to login to the remote machine to tunnel port 8000 on REMOTE locally.
Then you can do all the work on remote and access remote port 8000 with *http://localhost:8000*

### Persistent storage
  - Make sure that the directory ```/subdomain-data``` exists and is writable
    - ``` sudo mkdir /subdomain-data; sudo chmod o+w /subdomain-data;```
    - ```cd /subdomain-data;``` 
    - ```sudo mkdir -p db14 backups CACHE workqueue```
    - ```sudo chmod -R o+w /subdomain-data```


### Usage
  - git clone https://github.com/opentaproject/openta-public/ openta


### The user **super**
The username of superuser is **super**. In contrast to other superusers associated with each course, super is superuser for all courses and is set to the same password for every course.

### Minimal environment variables

Certain environment variables do not have defaults and **must be defined**.

- `PGUSER`  
  Cannot be easily changed; often sloppy set to *postgres*

- `PGPASSWORD`  
  Cannot be easily changed; often set to *postgres*

    - **Note** There may be authentication issues with the database. If you have trouble with that, you can modify the security settings with ```/subdomain-data/db14/pg_hba.conf```

- `SECRET_KEY='xxxxx'`  
  Can be anything; can be changed later; suitably a hash

- `SUPERUSER_PASSWORD`  
  Absolutely necesary for **`super`**  . Is not easily changed later.

- `POSTGRES_DEFAULT_DB='xxxxxx'`  
  Cannot be easily changed

### Test localhost

**Run a trivial docker test**

- `cd openta/openta/docker-compose`
- `docker compose -f test.yml up`

**Now inspect http://localhost:8000**

### Run openta in docker

Make sure that the environment variables exist (for example in `.envrc` or `.bashrc`).

- `cd openta/openta/docker-compose`
- `docker compose up --pull always --force-recreate`

**Now exec into the Docker image and create databases and cache**

- `docker ps`
- `docker exec -it XXXXXX bash`
- `psql -U ${PGUSER} -c "CREATE DATABASE ${POSTGRES_DEFAULT_DB} OWNER ${PGUSER} ;"`
- `python manage.py migrate`
- `python manage.py createcachetable`

**In the Docker image, create a course (for example `test1`)**

You can create many courses this way

- `python py_create_course test1`

**Exit the Docker image with ^D**
- Go to **http://test1.localhost:8000**
- Log in as `super` with the password `${SUPERUSER_PASSWORD}` and look around
  - *If your login is rejected the first time; try again*

**To take down the instance**

- `docker compose down --remove-orphans`

## Current OpenTA course owners

### Make a copy of exercises only
  - **You can make a exercises from a working copy to local**
    - On the active course, choose the **Course -> Export Exercises**
    - Save the zip file on your local computer
    - In your course on localhost, as super choose **Course -> Import Exercises**
    - Choose the zip file you just exported 
    - Wait until done; for many exercises it can take a couple of minutes
    - You should now have your exercises, with exercise opions imported

### Make a copy of of the entire course
  - **You can local copy of the entire course**
    - On the active course, choose the **Server -> Export**
    - Save the zip file on your local computer
    - As super on your local machine choose **Server -> Import**
    - Choose the zip file you just exported 
      - *If many students have been saving pdf results in large files*
      - *The resultant file can be several gigabytes and downloads may cause problems*
    - Wait until you see *Success - Log out*

## Creating new content your local server
  - See https://opentaserver.com for instructions in using the interface



