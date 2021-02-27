# Example OpenShift
```
export DOCKER_REPO=s53ostlund
oc login --token=sha256~xxxxxxx --server=https://130.241.39.203:6443
cp django/backend/backend/settings_production.py django/backend/backend/settings.py 

make build-deploy-docker
# check the push commands  docker push s53ostlund/openta:XXXXX && docker push s53ostlund/nginx:XXXXXXX
cd docker_deploy/kubernetes
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
./kube.py create-instance --subpath=subpath123 --docker-repo=s53ostlund  --output-path=.
./kube.py deploy-instance subpath123 # IGNORE INGRESS ERROR!
./kube.py list-instances
```
 
# Quick start
Setup a kubernetes cluster in your favorite way so that `kubectl` is authentication with a cluster.
For example with an OpenShift system first do
`oc login`
If running on minikube
`
minikube start
kubectl create namespace openta
kubectl config set-context --current --namespace=openta`
`

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


