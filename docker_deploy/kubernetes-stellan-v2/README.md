# Quick start
```
chmod +x ./kube.py
minikube delete
minikube start --cpus 4 --memory 8096 --driver=virtualbox # --extra-config=apiserver.runtime-config=apps/v1beta1=true,extensions/v1beta1/deployments=true
kubectl create namespace openta
minikube addons enable ingress
eval $(minikube docker-env)
docker login
kubectl delete secret dockerkey --namespace openta
kubectl create secret generic dockerkey --from-file=.dockerconfigjson=/Users/ostlund/.docker/config.json --type=kubernetes.io/dockerconfigjson
kubectl cluster-info
export DOCKER_REPO=s53ostlund
kubectl config set-context $(kubectl config current-context) --namespace=openta
kubectl apply -f ingress.yaml
export  SERVER_INFO_KEY=SERVER_INFO_KEY_FROM_KUBKOMMANDS # ANYTHING UNIQUE GOES HERE AS SERVER_INFO_KEY
export SUBPATH=subpathh
export VERSION=fim770v6_f50c17d1 #FROM make version in 
./kube.py create-instance --subpath=$SUBPATH --docker-repo=s53ostlund --version  $VERSION --server_info_key $SERVER_INFO_KEY --output-path=.
./kube.py deploy-instance $SUBPATH
./kube.py initialize-instance  $VERSION-XXXXX # GET XXXX kubectl get pods
## CONFIRM CONTAINER IS SERVING 
k exec -i -t subpathg-774cd8f49f-n2hdr  --container web -- /bin/bash
k port-forward deployment/subpathg  8000:8000 # NOT NGINX
k port-forward deployment/subpathnew 8080:8080 # OK!
k port-forward deployment/subpathh 8080:8080 # OK!

# dev cycle; for backend changes
# from base directory
docker build --tag s53ostlund/openta:v2.1.2 .
docker push 53ostlund/openta:v2.1.2 

# from kubernetetes-stellan-v2
docker build --tag s53ostlund/nginx:v2.1.2 .
docker push s53ostlund/nginx:v2.1.2 


```

## Setup a kubernetes cluster in your favorite way so that `kubectl cluster-info` returns a healthy cluster.
## Install an ingress controller such that
`kubectl get ingress --all-namespaces` is non-empty

## Prepare docker repo
Create or login to a docker repository
`docker login ...`

Build and push openta
`DOCKER_REPO=repo_name make build-deploy-docker`

Push images as instructed

Note openta version (referred to as openta-version below)
`make version`

## Create virtualenv
`python3 -m venv env`
`source env/bin/activate`
`pip install -r requirements.txt`

## List available commands
`./kube.py --help`

Help for a subcommand can be found with
`./kube.py command --help`

## Create a new instance
See `./kube.py create-instance --help` for full reference.
Example:
`./kube.py create-instance --subpath=example --docker-repo=repo_name --version openta-version --output-path=.`

Inspect the deployment in `$PWD/example`

Deploy the instance with
`./kube.py deploy-instance example`

### Inspect instances
`./kube.py list-instances`

Wait for the containers to come up

### Initialize instance
`./kube.py initialize-instance example`

### Connect to instance via tunnel
`./kube.py access-instance example`


