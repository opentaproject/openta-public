# Create a docker image frontend and backend 

- The important new files are in the subdirectory docker-build which contains two types of files
	- Dockerfile and .dockerignore which are used to build the docker image locally
	- docker-compose.yml, nginx.conf and settings.py which are loaded (by hand) to the cloud VM 
- The build tree should be clean clone from the repo s53ostlund/openta

## Create docker image from project base.
```
git clone https://s53ostlund/openta alpha-plus-clean
cd alpha-plus-clean
git checkout docker-build
```
## Build frontend
```
cd frontend
npm install
brunch build
```
## build backend

- The main reason for installing this locally is to successfully run the collectstatic command
- If not for that, it seems we don't have to construct a complete local environment

```
cd ../django
virtualenv -p python3 env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd backend
python manage.py collectstatic
```

## build dockerfile from project base

- Note .dockerignore ignores the env just build
- The Dockerfile in docker-build is linked to Dockerfile in base
- Execute the following commands from project base

```
cp docker-build/Dockerfile .
cp docker-build/.dockerignore .
docker build --tag s53ostlund/openta:alpha-plus .
docker tag s53ostlund/openta:openta-image openta-image
```


# docker-openta remove stuff ; dangerous commands!
```
alias remove-all-images=' docker stop $(docker ps -aq) && \
	docker rm $(docker ps -aq) && \
	docker rmi $(docker images -q) --force'
docker network prune
docker voluem prune
```

# Create vm instance in google cloud

## VM instances
- name - something you remember
- Compute series E2
- Machine type e2-standard (change this later to e2-small when running)
- Image - custom - Container-optimized OS OS-77-12371
- Allow http and https
- Get a FQDM and point it to the VM instanc

## VPC Networks

- External IP addresses - reserve static IP address
- name it something and attach it to the VM


## VM instances

- Get the ssh gcloud command but remove the ''beta'' in the string if it is there
- execute the ssh command and log in to the instance

See

- ( https://cloud.google.com/dns )
- ( https://stackoverflow.com/questions/62493334/ssl-certificate-on-container-optimized-os-docker )

```
gcloud compute ssh --zone "europe-north1-b" "opentaproject" --project "demoproject-296306"
```
- Copy the files in the docker-build directory to the VM
- Then do the commands

```
alias docker-compose="docker run -v /var/run/docker.sock:/var/run/docker.sock -v "$PWD:$PWD" -w="$PWD" docker/compose:1.24.0" >> ~/.bashrc
source .bashrc
docker pull s53ostlund/openta:alpha-plus
docker tag s53ostlund/openta:alpha-plus openta-image
export OPENTA_SUBPATH=openta
docker-compose up
<<<<<<< HEAD

#Add .dockerignore
```
###
- Check https://opentaproject.com/openta
