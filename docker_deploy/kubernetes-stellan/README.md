# Quick start assuming images exist at repo
```
chmod +x ./kube.py
minikube delete
minikube start --cpus 4 --memory 8096 --vm-driver virtualbox # --driver=virtualbox # --extra-config=apiserver.runtime-config=apps/v1beta1=true,extensions/v1beta1/deployments=true
kubectl create namespace openta
minikube addons enable ingress
eval $(minikube docker-env)
kubectl delete secret dockerkey --namespace openta
```
## Tricky; do this once only;   Get the right secret into minikube


- `minikube ssh`
- inside minikube : `cat ~docker/.docker/config.json`
- copy this file to your $HOME/.docker/config.json.minikube 

##  Now continue
```
kubectl create secret generic dockerkey --from-file=.dockerconfigjson=/Users/ostlund/.docker/config.json.minikube --type=kubernetes.io/dockerconfigjson --namespace openta
kubectl cluster-info
export DOCKER_REPO=s53ostlund
kubectl config set-context $(kubectl config current-context) --namespace=openta
kubectl apply -f ingress.yaml
export  SERVER_INFO_KEY=SERVER_INFO_KEY_FROM_KUBKOMMANDS # ANYTHING UNIQUE GOES HERE AS SERVER_INFO_KEY
export SUBPATH=subpathclean7
export VERSION=clean7
export VERSION_TAG=clean7
source env/bin/activate
./kube.py create-instance --subpath=$SUBPATH --docker-repo=s53ostlund --version  $VERSION --version_tag  $VERSION_TAG --server_info_key $SERVER_INFO_KEY --output-path=.
./kube.py deploy-instance $SUBPATH
./kube.py initialize-instance  $VERSION-XXXXX # GET XXXX kubectl get pods
k exec -i -t subpathg-774cd8f49f-n2hdr  --container web -- /bin/bash
k port-forward deployment/subpathg  8000:8000 # NOT NGINX
k port-forward deployment/subpathnew 8080:8080 # OK!
k port-forward deployment/subpathh 8080:8080 # OK!

```
# dev cycle; for backend changes

## from base directory
```
git clone https://github.com/s53ostlund/openta.git wip
cd wip ; git checkout wip;
docker login
```
## Build the base image; do at most once openta-base is not used
```
docker build --tag s53ostlund/openta:openta-base -f docker-build/Dockerfile-base .
docker push s53ostlund/openta:openta-base
```
## Build the backend image 
```
export VERSION_TAG=clean7
cp django/backend/backend/settings_production_kubernetes.py django/backend/backend/settings.py
cp docker-build/.dockerignore .
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
cd ..
python3 -m venv env
pip install  -r requuirements.txt
cd django
python manage.py collectstatic
export PROJECT_ID=$(gcloud config list --format='value(core.project)')
export PROJECT_ID_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export INSTANCE_NAME='demoproject'
export REGION='europe-north1'
export INSTANCE_CONNECTION_NAME=${PROJECT_ID}:${REGION}:${INSTANCE_NAME}
export BUCKET_NAME=openta-cdn-bucket
gsutil -m cp -r deploystatic gs://${BUCKET_NAME}/${VERSION_TAG}
```

## Build the backend nginx image


```
cd docker_deploy/kubernetes-stellan-v2/nginx
docker build --tag s53ostlund/nginx:${VERSION_TAG} -f Dockerfile.nginx .

```

- Try out runserver and make sure CDN is serving frontend $VERSION_TAG 
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
