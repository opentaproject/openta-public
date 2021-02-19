# (* https://www.youtube.com/watch?v=mZQzPAUH2Lc&feature=youtu.be *)
# (* https://karlstoney.com/2017/03/01/fuse-mount-in-kubernetes/ *)
# https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/
# https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/gce-pd-csi-driver 
# provision storage; google is too expensive since 1Gb minimum
export PROJECT_NAME=production
export PROJECT_ID=production-304119
export PROJECT_NUMBER=244333042069
export CLUSTER_NAME=opentaproject-com-cluster
export COMPUTE_ZONE=europe-west3-a
export REGION=europe-west3

gcloud init
kubectl create namespace openta-prod
kubectl config set-context --current --namespace=openta-prod

# https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/preexisting-pd
#k apply -f existing-pd.yaml


gcloud container clusters create $CLUSTER_NAME --zone $COMPUTE_ZONE \
	--release-channel stable\
        --num-nodes=1  \
        --machine-type=e2-standard-2  \
        --addons=GcePersistentDiskCsiDriver  \
        --scopes=cloud-platform,storage-full,storage-rw 
# https://medium.com/emvi/wildcard-ssl-certificates-on-kubernetes-using-acme-dns-fde583a69eb5
#https://stackoverflow.com/questions/60675083/how-to-use-wildcard-certificates-from-let-s-encrypt-with-cert-manager
# I followed the next one
# https://medium.com/@kpsrinivas/wildcard-ssl-using-lets-encrypt-for-kubernetes-ingress-gke-ff7e2d60e911
# generate the fullchain and privkey
k create secret tls opentaproject-com-secret --cert  ./fullchain.pem --key ./privkey.pem 


helm repo update 
kubectl create namespace cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --version v1.1.0  --set installCRDs=true


#k create -f pd-example-class.yaml
#k create -f pvc-example.yaml
# THE REASON FOR USING THE nginx-ingress is to get around
# THE quota restriction with gce-ingress where only 5 routes are allowed
#source ./createsecret # which is not in git repo
# kubectl create secret docker-registry dockerkey --docker-server=https://index.docker.io/v1/  --docker-username=XXXXX --docker-password=XXXXX --docker-email=stellan.ostlund@gmail.com

gcloud container clusters get-credentials $CLUSTER_NAME --zone $COMPUTE_ZONE --project $PROJECT_ID
kubectl create clusterrolebinding cluster-admin-binding   --clusterrole cluster-admin   --user $(gcloud config get-value account)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install my-mc-ingress ingress-nginx/ingress-nginx  --set rbac.create=true   --set controller.service.loadBalancerIP=35.234.115.40 
# FIRST TIME, GET THE ingress IP and send DNS to that
#kubectl scale deployment my-mc-deployment --replicas  1
# DO  THE FOLLOWING ONLY ONCE to create a named IP address
# gcloud compute addresses create pts-address --global
# 
#gcloud compute addresses describe pts-address-regional 
# See https://cert-manager.io/docs/tutorials/acme/ingress/
# ENABLE SSH AND CERTS




#kubectl apply -f test-resources.yaml
#kubectl describe certificate -n cert-manager-test
#kubectl apply -f letsencrypt-staging.yaml
# CHECK EVERYTING IS OK
#kubectl describe secret pts-local-issuer-account-key
kubectl apply -f letsencrypt-prod.yaml
k apply -f yamls
# COMMENT/UNCOMMENT staging/production lines in ingress.yaml
#kubectl apply -f production-issuer.yaml
# RENEW CERTIFICATE by deleting the old
k delete secret pts-local-issuer-account-key
k describe certificate pts-local-issuer-account-key


# ENABLE NGINX-INGRESS
kubectl apply -f yamls
kubectl --namespace default get services -o wide -w my-mc-ingress-ingress-nginx-controller
k port-forward deployment/${SUBPATH} 8080:8080
#kubectl describe managedcertificate my-mc-certificate-1
kubectl describe ingress my-mc-ingress 
k describe secret letsencrypt-prod
#kubectl describe managedcertificate my-mc-certificate-1
gcloud compute backend-services list
# NOTE THAT THIS INGRESS HITS THE LIMIT quota=5 for backend services
# TAKES ABOUT 8-25 MINUTES TO PROVISION AND MAKE VISIBLE
# IN THE MEANTIME http may work and https gives failueres
# EVEN AFTER curl works, webpage may fail for another few minutes
# https://v2.pinetreesquare.com
# https://pinetreesquare.com/mynginx/12345
# https://pinetreesquare.com/webtwo/a
# PAUSE THE CLUSTER 
gcloud container clusters resize $CLUSTER_NAME --node-pool default-pool --num-nodes 1
#kubectl scale deployment my-mc-deployment --replicas 2
#https://www.youtube.com/watch?v=X48VuDVv0do
#Cleanup
#gcloud init
# DELETE THE CLUSTER
gcloud container clusters delete  $CLUSTER_NAME
# LOOK FOR LOADBALANCERS TO DELETE

# TRICKY TO CHANGE SCOPES
# (* https://adilsoncarvalho.com/changing-a-running-kubernetes-cluster-permissions-a-k-a-scopes-3e90a3b95636 *)
gcloud container node-pools create newpool --cluster $CLUSTER_NAME --machine-type e2-standard-2 --scopes https://www.googleapis.com/auth/devstorage.read_write
gcloud container node-pools create newpool2 --cluster $CLUSTER_NAME --machine-type e2-standard-2 --scopes https://www.googleapis.com/auth/devstorage.read_write

