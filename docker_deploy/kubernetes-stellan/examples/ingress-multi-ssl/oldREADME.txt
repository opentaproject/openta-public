## SELF-SIGNED CERTIFICATE 
#- Follow (https://cloud.google.com/kubernetes-engine/docs/how-to/ingress-multi-ssl#pre-shared-certs)
#gcloud init
#gcloud info
#export COMPUTE_ZONE=europe-north1-b
#export PROJECT_ID=demoproject-296306
#export CLUSTER_NAME=cluster-1
#export REGION=europe-north1
#gcloud container clusters create cluster-name --zone compute-zone --node-locations compute-zone,compute-zone
#gcloud container clusters get-credentials cluster-1 --zone europe-north1-b --project demoproject-296306
#kubectl apply -f my-mc-deployment.yaml
#kubectl apply -f my-mc-service.yaml
#openssl genrsa -out test-ingress-1.key 2048
#openssl req -new -key test-ingress-1.key -out test-ingress-1.csr  -subj "/CN=pinetreesquare.com"
#openssl x509 -req -days 365 -in test-ingress-1.csr -signkey test-ingress-1.key -out test-ingress-1.crt
#openssl genrsa -out test-ingress-2.key 2048
#openssl req -new -key test-ingress-2.key -out test-ingress-2.csr  -subj "/CN=v2.pinetreesquare.com"
#openssl x509 -req -days 365 -in test-ingress-2.csr -signkey test-ingress-2.key -out test-ingress-2.crt
#
#
#export FIRST_CERT_FILE="test-ingress-1.crt"
#export FIRST_KEY_FILE=test-ingress-1.key
#export FIRST_DOMAIN=pinetreesquare.com
#export FIRST_SECRET_NAME=test-ingress-1-secret-name
#kubectl create secret tls ${FIRST_SECRET_NAME} --cert ${FIRST_CERT_FILE} --key  ${FIRST_KEY_FILE}
#
#
#export SECOND_CERT_FILE="test-ingress-2.crt"
#export SECOND_KEY_FILE=test-ingress-2.key
#export SECOND_DOMAIN=v2.pinetreesquare.com
#export SECOND_SECRET_NAME=test-ingress-2-secret-name
#kubectl create secret tls ${SECOND_SECRET_NAME} --cert ${SECOND_CERT_FILE} --key  ${SECOND_KEY_FILE}
#
#kubectl apply -f my-mc-ingress.yaml
## WAIT A FEW MINUTES
#kubectl describe ingress my-mc-ingress | grep Address
## THIS HAS CREATED A SELF-SIGNED  CERTIFICATE ; BUMMER

# MANAGED CERTIFICATE 

#export ADDRESS_NAME=pinetreesquaredotcom
#gcloud compute addresses create pinetreesquaredotcom --global
#gcloud compute addresses describe ${ADDRESS_NAME} --global

# SEE https://cloud.google.com/kubernetes-engine/docs/how-to/managed-certs
gcloud init
gcloud container clusters create cluster-1 --zone europe-north1-b --node-locations europe-north1-b --num-nodes=2
kubectl create secret docker-registry dockerkey --docker-server=https://index.docker.io/v1/  --docker-username=s53ostlund --docker-password=E95ostlund --docker-email=stellan.ostlund@gmail.com
gcloud container clusters get-credentials cluster-1 --zone europe-north1-b --project demoproject-296306
# DO  THE FOLLOWING ONLY ONCE
gcloud compute addresses create pts-address --global
# 
gcloud compute addresses describe pts-address --global
kubectl apply -f yamls
kubectl describe managedcertificate my-mc-certificate-1
kubectl describe ingress my-mc-ingress 
kubectl describe managedcertificate my-mc-certificate-1
# TAKES ABOUT 25 MINUTES TO PROVISION AND MAKE VISIBLE
# IN THE MEANTIME http may work and https gives failueres
# EVEN AFTER curl works, webpage may fail for another few minutes
# https://v2.pinetreesquare.com
# https://pinetreesquare.com
# DELETE WITH EITHER OF THESE
gcloud container clusters delete  cluster-1
gcloud container clusters resize loadbalancedcluster  --node-pool default-pool --num-nodes 0
#kubectl scale deployment my-mc-deployment --replicas 2
# https://www.youtube.com/watch?v=X48VuDVv0do


#Cleanup
#gcloud init
gcloud container clusters delete  cluster-1
