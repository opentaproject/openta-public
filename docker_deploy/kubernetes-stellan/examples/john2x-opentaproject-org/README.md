#https://john2x.com/blog/wildcard-certs-from-lets-encrypt-cert-manager-ingress-nginx-gke.html

export PROJECT_NAME=production
export PROJECT_ID=production-304119
export PROJECT_NUMBER=244333042069
export CLUSTER_NAME=opentaproject_org_cluster
export COMPUTE_ZONE=europe-west3-a
export REGION=europe-west3


export PROJECT_NAME=production
export PROJECT_ID=development-303921
export PROJECT_NUMBER=208179878135
export CLUSTER_NAME=opentaproject-org-cluster
export COMPUTE_ZONE=europe-west3-a
export REGION=europe-west3

gcloud init
#kubectl config set-context --current --namespace=default
#add google nameservers to new nameservers  
# FOLLOW john2x instructions 
# CloudDNS -> Zones 
#dig NS opentaproject.org
#opentaproject.org.	21441	IN	NS	ns-cloud-b4.googledomains.com.
#opentaproject.org.	21441	IN	NS	ns-cloud-b1.googledomains.com.
#opentaproject.org.	21441	IN	NS	ns-cloud-b2.googledomains.com.
#opentaproject.org.	21441	IN	NS	ns-cloud-b3.googledomains.com.
#
#
#docker login
#docker pull john2x/opentaproject_org
#docker run -p 8080:8080 john2x/opentaproject_org
#docker ps
# STOP THE RUNNING CONTAINER

gcloud container clusters create $CLUSTER_NAME --zone $COMPUTE_ZONE \
	--release-channel stable\
        --num-nodes=1  \
        --machine-type=e2-standard-2  \
        --addons=GcePersistentDiskCsiDriver  \
        --scopes=cloud-platform,storage-full,storage-rw 

kubectl create namespace opentaproject-org
k get namespace
#NAME              STATUS   AGE
#default           Active   77s
#kube-node-lease   Active   78s
#kube-public       Active   79s
#kube-system       Active   79s
#opentaproject_org     Active   17s

# SET DEFAULT NAMESPACE
# GET SIMPLE SERVICE RUNNING 
k apply -f 01-deployment.yaml
k apply -f 02-service.yaml

kubectl config set-context --current --namespace=opentaproject-org
kubectl port-forward svc/wildcard-demo 8080:80 

# check asdf.localhost:8080
# Now install nginx-ingress

gcloud container clusters get-credentials $CLUSTER_NAME --zone $COMPUTE_ZONE --project $PROJECT_ID
kubectl create clusterrolebinding cluster-admin-binding   --clusterrole cluster-admin   --user $(gcloud config get-value account)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx  --set rbac.create=true  --namespace opentaproject-org --set controller.service.loadBalancerIP=35.242.192.41 
kubectl get service ingress-nginx-controller --namespace=opentaproject-org

# make the ingress IP static and uncomment loadBalancerIP for reuse

# FIX THE A-RECORDS AT GOOGLE
# default.opentaproject.org. A    34.89.179.164
# opentaproject.org.        A    34.89.179.164
# *.opentaproject.org.      A    34.89.179.164

# INSTALL cert-manager 
helm repo update 
kubectl create namespace cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --version v1.1.0  --set installCRDs=true

kubectl apply -f test-resources.yaml
# CHECK that the certificate was successuflly issued
# https://cert-manager.io/docs/installation/kubernetes/
kubectl describe certificate -n cert-manager-test
kubectl delete -f test-resources.yaml

# Go to your Google Cloud Console and navigate to IAM & Admin > Service accounts. 
# From there, create a new service account, assigning it a recognizable name and grant it 
# access to the “DNS Administrator” role. Save and then download the key
# in the JSON format and save it to a file that is here production....


kubectl create secret generic clouddns-service-account  \
	--from-file=service-account-key.json=development-303921-4190c76f4d71.json \
	--namespace=opentaproject-org

# AT THIS POINT THE TUTORIAL BREAKS DOWN
# SEE https://cert-manager.io/docs/configuration/acme/dns01/google/

gcloud iam service-accounts create dns01-solver-org
gcloud iam service-accounts keys create key.json --iam-account dns01-solver-org@development-303921-4190c76f4d71.json
# created key [4096f9a17a2517de83f1d5d942fec0702e0dbd5b] of type [json] as [key.json] 
# for [dns01-solver@production-304119.iam.gserviceaccount.com]
kubectl create secret generic clouddns-dns01-solver-svc-acct --from-file=key.json --namespace=opentaproject-org

# GET http://opentaproject.org working
# GET http://jimbo.opentaproject.org working

k apply -f 03-ingress-wildcard-demo.yaml

# NOW GET STAGING ISSUER 
k apply -f 04a-issuer-ingress-nginx-staging.yaml

# MAKE SURE THAT letsencrypt-staging is active
k get issuers
# now get certificate 
k apply -f 05a-certificate.yaml

# THIS IS THE MOST FRAGILE PART OF THE PROCESS
# IT TAKES ABOUT 6 minutes until k get certificates shows READY

k describe orders
k describe certificaterequests
k describe certificates
k get certificates


# ###########

k apply -f 06b-ingress-staging.yaml

# try curl https://default.opentaproject.org -i -k
curl -vvI https://default.opentaproject.org -i  -k 
# MAKE SURE LE X1 certificate is included

kubectl config set-context --current --namespace=opentaproject-org


# Now do it in opentaproject_org namespace
#kubectl create secret generic clouddns-service-account \
#	--from-file=service-account-key.json=development-303921-4190c76f4d71.json \
#	--namespace=opentaproject-org
#
#k apply -f 07a-ingress-default-http-backend.yaml
#k apply -f 08a-certificate-wildcard-demo-staging.yaml
#k apply -f 09-ingress-default-http-backend.yaml
##k describe ingresses
#
## WAIT UNTIL IT IS NO LONGER SCHEDULED FOR SYNC

curl https://opentaproject.org -i -k
curl https://jimbo.opentaproject.org -i -k
curl https://gumbo.opentaproject.org -i -k

#10a-issuer-opentaproject_org-prod.yaml
#11a-certificates-opentaproject_org-prod.yaml
#12-ingress-opentaproject_org-prod.yaml
