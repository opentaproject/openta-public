export PROJECT_NAME=production
export PROJECT_ID=production-304119
export PROJECT_NUMBER=244333042069
export CLUSTER_NAME=opentaproject-com-cluster
export COMPUTE_ZONE=europe-west3-a
export REGION=europe-west3


#export PROJECT_NAME=development
#export PROJECT_ID=development-303921
#export PROJECT_NUMBER=208179878135
#export CLUSTER_NAME=opentaproject-org-cluster
#export COMPUTE_ZONE=europe-west3-a
#export REGION=europe-west3

# PREPARATION 
# Go to your Google Cloud Console and navigate to IAM & Admin > Service accounts. 
# From there, create a new service account, assigning it a recognizable name and grant it 
# access to the “DNS Administrator” role. Save and then download the key and copy
# THE IP variable is filled in after the first time the load balancer is created
# and the Ephemeral IP is converted to static

export KEYFILE=development-303921-4190c76f4d71.json 
export KEYFILE=production-304119-24bfd8ef3fe2.json
export IP=34.89.179.164


gcloud init
gcloud container clusters create $CLUSTER_NAME --zone $COMPUTE_ZONE \
	--release-channel stable\
        --num-nodes=1  \
        --machine-type=e2-standard-2  \
        --addons=GcePersistentDiskCsiDriver  \
        --scopes=cloud-platform,storage-full,storage-rw 
kubectl create namespace opentaproject-com
gcloud container clusters get-credentials $CLUSTER_NAME --zone $COMPUTE_ZONE --project $PROJECT_ID
kubectl create clusterrolebinding cluster-admin-binding   --clusterrole cluster-admin   --user $(gcloud config get-value account)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx  --set rbac.create=true  --namespace opentaproject-com   --set controller.service.loadBalancerIP=${IP}

# FIRST TIME AFTER RUNNING THIS FIX UP THE INSTALLATION BY SETTING
# A STATIC IP WITH THE IP OF THE LOAD BALANCER AND UNCOMMENT THE LINE ABOVE
# AND PUT IT INTO THE IP variable

kubectl get service ingress-nginx-controller --namespace=opentaproject-com
helm repo update 
kubectl create namespace cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --version v1.1.0  --set installCRDs=true
kubectl create secret generic clouddns-service-account-opentaproject-com  \
	--from-file=service-account-key.json=${KEYFILE} \
	--namespace=opentaproject-com
gcloud iam service-accounts create dns01-solver-opentaproject-com
gcloud iam service-accounts keys create key.json --iam-account dns01-solver-opentaproject-com@production-304119.iam.gserviceaccount.com
k apply -f yamls-staging
kubectl config set-context --current --namespace=opentaproject-com

# NOW SET A-RECORDS on CloudDNS and fix IP to static and  remove # in helm install and set variable IP
#WHEN ALL DONE , after perhaps 6 minutes
# FOR DEBUGGING 
k get orders
k get challenges
k get certificaterequests
k get certificates
k describe challenges
k describe orders
k describe certificaterequests
k describe certificates

# Certificate READY = False and challenges permission fails
# is usually because service account is not properl
# set up. See PREPARATION


curl https://opentaproject.com  -k 
# yields X1 certificate 
# then 
k apply -f yamls-production
# then wait another 6-10 minutes

