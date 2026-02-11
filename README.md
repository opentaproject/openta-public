# OpenTA web platform

OpenTA is a web platform for engineering and science courses at the university level. It has been
used for many years at Chalmers and Gothenburg University.

More information about OpenTA and documentation can be found here:
[https://opentaproject.com](https://opentaproject.com).

## Requirements

To run OpenTA with the following instructions you need to install Docker and Git.

## Installation using Docker

This initial release documents shows how to install the platform on a private Linux server. The easiest
method is Docker. OpenTA and its libraries (such as povray, mathplot, and LaTeX) are a large package,
so plan for at least 8 GB of memory. A VPS can be a good option to avoid cluttering your own machine.

## Installing on a remote VPS

You can install OpenTA on your local Linux machine and use localhost. Another option is to install
on a VPS and connect via SSH. Use the following command to tunnel port 8000 from the remote machine
to your local machine:

```bash
ssh -q -L 8000:localhost:8000 USER@REMOTE
```

Then access the remote instance at [http://localhost:8000](http://localhost:8000).

### Persistent storage

OpenTA needs to store files on the machine it runs on. Make a writable directory DATA_MOUNT for instance DATA_MOUNT=/tmp/mnt/pv that will be persistent. TThe following command creates the required
folders and assigns the right permissions.

```bash
sudo mkdir -p /subdomain-data \
    /subdomain-data/db14 \
    /subdomain-data/backups \
    /subdomain-data/CACHE \
    /subdomain-data/workqueue
sudo chmod -R o+w /subdomain-data
```

### Usage

The following command retrieves the files required to run OpenTA.

```bash
cd __install_folder__
git clone https://github.com/opentaproject/openta-public/ openta
```

Replace `__install_folder__` with the name of the folder (directory) you want to install OpenTA in.

### The *super* user

The super username has unrestricted system access. Unlike course-specific superusers, this global
account works across all courses and uses the same password for every instance.

### Minimal environment variables

Certain environment variables do not have defaults and **must be defined**.

- `PGUSER`
    - The PostgreSQL role name used by OpenTA. Cannot be easily changed; often sloppy set to `postgres`.

- `PGPASSWORD`
    - The password used by `PGUSER` role. Cannot be easily changed; often set to `postgres`.

    - **Note:** There may be authentication issues with the database. If you have trouble with that,
      you can modify the security settings in `/subdomain-data/db14/pg_hba.conf`.

- `SECRET_KEY='xxxxx'`
    - Can be anything; can be changed later; suitably an MD5 hash.

- `SUPERUSER_PASSWORD`
    - Required for the `super` account and cannot be easily changed after initial install.

- `POSTGRES_DEFAULT_DB='xxxxxx'`
    - Cannot be easily changed after initial install.

- `DJANGO_SECRETS_FILE='stub'`
    - This is a stub for more more functionality not addressed in this early release document.
- `DATA_MOUNT`
  - The host base directory on which /subdomain-data/ is served in the container

### Test localhost

**Run a trivial Docker test**

```bash
cd __install_folder__
cd openta/openta/docker-compose
docker compose -f test.yml up
```

Replace `__install_folder__` with the folder you selected above.

Now open up this link in your browser: [http://localhost:8000](http://localhost:8000). You should see this:

```
Hello from localhost
```

### Run OpenTA in Docker

1. Create a `.envrc` file with the following variables:

    ```conf
    PGUSER=changeme
    PGPASSWORD=changeme
    SECRET_KEY=changeme
    SUPERUSER_PASSWORD=changeme
    POSTGRES_DEFAULT_DB=changeme  # ANYTHING BUT NOT 'default'
    DATA_MOUNT=changeme 
    ```
    Replace `changeme` with suitable values.


1. Load the `.envrc` settings into your current shell. Either automatically or using the commands below.

    ```bash
    set -a; source .envrc; set +a
    ```

1. Start the Docker containers:

    ```bash
    cd __install_folder__/openta/docker-compose
    docker compose up -d --pull always --force-recreate
    ```

1. Create the database and cache:

    ```bash
    docker compose exec app psql -U ${PGUSER} -c "CREATE DATABASE ${POSTGRES_DEFAULT_DB} OWNER ${PGUSER};"
    docker compose exec app python /srv/openta/django/backend/manage.py migrate
    docker compose exec app python /srv/openta/django/backend/manage.py createcachetable
    ```

    You can ensure the database has been created using this command:

    ```bash
    docker compose exec app psql -U ${PGUSER} -c "\l"
    ```

    You should see a database with the name you selected for `POSTGRES_DEFAULT_DB` listed in the output of the command.

1. Create a course (for example `test1`):

    You can create many courses with this command:

    ```bash
    docker compose exec app python py_create_course test1
    ```

1. Open [http://test1.localhost:8000](http://test1.localhost:8000) in your browser.

    Log in with username `super` and the password you selected for `SUPERUSER_PASSWORD`.

    *If your login is rejected the first time, try again.*

1. To stop OpenTA:

    ```bash
    cd __install_folder__/openta/docker-compose
    docker compose down --remove-orphans
    ```

## Current OpenTA course owners

### Make a copy of exercises only
  - **Copy exercises from a working course to localhost**
    - On the active course, choose **Course -> Export Exercises**
    - Save the zip file on your local computer
    - On localhost, as super choose **Course -> Import Exercises**
    - Choose the zip file you exported
    - Wait until done; for many exercises it can take a couple of minutes
    - You should now have your exercises, with exercise options imported

### Make a copy of the entire course
  - **Copy the entire course to localhost**
    - On the active course, choose **Server -> Export**
    - Save the zip file on your local computer
    - As super on your local machine choose **Server -> Import**
    - Choose the zip file you exported
      - *If many students have been saving PDF results in large files, the export can be several
        gigabytes and downloads may cause problems.*
    - Wait until you see *Success - Log out*

## Creating new content on your local server
  - See https://opentaserver.com for instructions on using the interface.
