# Quickstart GKE
# make sure kubectl is served by gcloud commands
which gcloud # "/Users/ostlund/google-cloud-sdk/bin/kubectl"
gcloud init
export COMPUTE_ZONE=europe-north1-b
export PROJECT_ID=demoproject-296306
export CLUSTER_NAME=cluster-1
gcloud container clusters create ${CLUSTER_NAME} --zone ${COMPUTE_ZONE} --node-locations ${COMPUTE_ZONE}  
kubectl create namespace openta
kubectl config set-context $(kubectl config current-context) --namespace=openta
kubectl config set-context --current --namespace=openta
gcloud container clusters get-credentials cluster-1 --zone europe-north1-b --project demoproject-296306
kubectl cluster-info
export SERVER_INFO_KEY=SERVER_INFO_KEY_FROM_KUBKOMMANDS # ANYTHING UNIQUE GOES HERE AS SERVER_INFO_KEY
export VERSION=alpha-plus_69259d1f 
export VERSION_TAG=v2.1.2
export SUBPATH=v212b
export DOCKER_REPO=s53ostlund
#./kube.py create-instance --subpath=$SUBPATH --docker-repo=s53ostlund --version  $VERSION --version_tag  $VERSION_TAG --server_info_key $SERVER_INFO_KEY --output-path=.
docker login
kubectl delete secret dockerkey --namespace openta
kubectl config set-context --current --namespace=openta create secret generic dockerkey --from-file=.dockerconfigjson=$HOME/.docker/config.json.gke --type=kubernetes.io/dockerconfigjson --namespace openta
kubectl create secret docker-registry dockerkey --docker-server=https://index.docker.io/v1/  \
	--docker-username=XXXXX --docker-password=XXXXX --docker-email=stellan.ostlund@gmail.com
kubectl apply -f v212b 
gcloud container clusters resize cluster-1 --node-pool default-pool --num-nodes 1



# Quick start minikube assuming images exist at repo
```
chmod +x ./kube.py
minikube delete
minikube start --cpus 4 --memory 8096 --vm-driver virtualbox # --driver=virtualbox # --extra-config=apiserver.runtime-config=apps/v1beta1=true,extensions/v1beta1/deployments=true
kubectl create namespace openta
minikube addons enable ingress
eval $(minikube docker-env)
kubectl delete secret dockerkey --namespace openta
```
## Tricky; Try this; I can't get minikube consistently set secret properly


- `minikube ssh`
- inside minikube : `cat ~docker/.docker/config.json`
- copy this file to your $HOME/.docker/config.json.minikube 

##  Now continue
```
kubectl create secret generic dockerkey --from-file=.dockerconfigjson=$HOME/.docker/config.json.minikube --type=kubernetes.io/dockerconfigjson --namespace openta
kubectl cluster-info
export DOCKER_REPO=s53ostlund
kubectl config set-context --current --namespace=openta
kubectl config set-context $(kubectl config current-context) --namespace=openta
kubectl apply -f ingress.yaml
export  SERVER_INFO_KEY=SERVER_INFO_KEY_FROM_KUBKOMMANDS # ANYTHING UNIQUE GOES HERE AS SERVER_INFO_KEY
source env/bin/activate
export VERSION=alpha-plus_abd1ee9f
export VERSION_TAG=v2.1.2
export SUBPATH=v212b
./kube.py create-instance --subpath=$SUBPATH --docker-repo=s53ostlund --version  $VERSION --version_tag  $VERSION_TAG --server_info_key $SERVER_INFO_KEY --output-path=.
./kube.py deploy-instance $SUBPATH
./kube.py initialize-instance  $VERSION-XXXXX # GET XXXX kubectl get pods
k exec -i -t subpathclean7-765558fcc9-ctqbc --container web -- /bin/bash
k port-forward deployment/${SUBPATH} 8080:8080 # OK!

```
# dev cycle; for backend changes

## from base directory
```
git clone https://github.com/s53ostlund/openta.git alpha-plus
cd alpha-plus; git checkout alpha-plus;
docker login
```
## Build the base image; do at most once openta-base is not used

- important: do this from a clean repo, or a bunch of extra files will be included
- env and modules directories should not exist

```
docker build --tag s53ostlund/openta:openta-base -f docker-build/Dockerfile-base .
docker push s53ostlund/openta:openta-base
```
## Build the backend image 

```
export VERSION_TAG=${CURRENT_TAG}
export VERSION=alpha-plus_bff9a87b
cp django/backend/backend/settings_production_kubernetes.py django/backend/backend/settings.py
ln -s docker-build/.dockerignore .dockerignore
docker build --tag s53ostlund/openta:${VERSION_TAG} .
docker push s53ostlund/openta:${VERSION_TAG}

```

## Build the frontend CDN

- See cdn subdirectorr for instructions for setting up cdn
- Tricky issue with cors permssion and font-awesome

```
cd frontend
npm install
brunch build
cd ../django
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install  -r requirements.txt
cd django
python manage.py collectstatic
export PROJECT_ID=$(gcloud config list --format='value(core.project)')
export PROJECT_ID_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export INSTANCE_NAME='demoproject'
export REGION='europe-north1'
export INSTANCE_CONNECTION_NAME=${PROJECT_ID}:${REGION}:${INSTANCE_NAME}
export BUCKET_NAME=openta-cdn-bucket
# MAKE SURE keyfile.json is in place
gsutil -m cp -r deploystatic gs://${BUCKET_NAME}/${VERSION_TAG}
```

## Build the backend nginx image


```
cd ..
cd docker_deploy/kubernetes-stellan/nginx
docker build --tag s53ostlund/nginx:${VERSION_TAG} -f Dockerfile.nginx .

```

- Try out runserver and make sure CDN is serving frontend $VERSION_TAG 

```
cd django
source env/bin/activate
cd backend
./manage.py migrate
./manage.py loaddata fixtures/auth.json
./manage.py loaddata fixtures/course.json
./manage.py createcachetable


- Setup a kubernetes cluster in your favorite way so that `kubectl cluster-info` returns a healthy cluster.
## Install an ingress controller such that
`kubectl get ingress --all-namespaces` is non-empty

## List available commands
`./kube.py --help`

Help for a subcommand can be found with
`./kube.py command --help`

### Inspect instances
`./kube.py list-instances`

Wait for the containers to come up

### Initialize instance
`./kube.py initialize-instance example`

### Connect to instance via tunnel
`./kube.py access-instance example`
