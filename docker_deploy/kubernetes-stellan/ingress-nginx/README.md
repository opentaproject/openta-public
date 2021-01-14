gcloud init
gcloud container clusters create cluster-1 --zone europe-north1-b --node-locations europe-north1-b --num-nodes=2  --machine-type=e2-standard-2 
# THE REASON FOR USING THE nginx-ingress is to get around
# THE quota restriction with gce-ingress where only 5 routes are allowed
# SEE source ./create_secret which is not in git repo
# kubectl create secret docker-registry dockerkey --docker-server=https://index.docker.io/v1/  --docker-username=XXXXX --docker-password=XXXXX --docker-email=stellan.ostlund@gmail.com
gcloud container clusters get-credentials cluster-1 --zone europe-north1-b --project demoproject-296306
kubectl create clusterrolebinding cluster-admin-binding   --clusterrole cluster-admin   --user $(gcloud config get-value account)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install my-mc-ingress ingress-nginx/ingress-nginx  --set rbac.create=true # --set controller.service.loadBalancerIP=130.211.32.53 
# FIRST TIME, GET THE ingress IP and send DNS to that
#kubectl scale deployment my-mc-deployment --replicas  1
# DO  THE FOLLOWING ONLY ONCE to create a named IP address
# gcloud compute addresses create pts-address --global
# 
#gcloud compute addresses describe pts-address-regional 
# See https://cert-manager.io/docs/tutorials/acme/ingress/
helm repo update 
kubectl create namespace cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --version v1.1.0  --set installCRDs=true
kubectl apply -f test-resources.yaml
kubectl describe certificate -n cert-manager-test
kubectl apply -f letsencrypt-staging.yaml
# CHECK EVERYTING IS OK
kubectl describe secret pts-local-issuer-account-key
k apply -f yamls
# COMMENT/UNCOMMENT staging/production lines in ingress.yaml
kubectl apply -f production-issuer.yaml
# RENEW CERTIFICATE by deleting the old
k delete secret pts-local-issuer-account-key
k describe certificate pts-local-issuer-account-key




kubectl apply -f yamls
kubectl --namespace default get services -o wide -w my-mc-ingress-ingress-nginx-controller
kubectl describe managedcertificate my-mc-certificate-1
kubectl describe ingress my-mc-ingress 
kubectl describe managedcertificate my-mc-certificate-1
gcloud compute backend-services list
# NOTE THAT THIS INGRESS HITS THE LIMIT quota=5 for backend services
# TAKES ABOUT 8-25 MINUTES TO PROVISION AND MAKE VISIBLE
# IN THE MEANTIME http may work and https gives failueres
# EVEN AFTER curl works, webpage may fail for another few minutes
# https://v2.pinetreesquare.com
# https://pinetreesquare.com/mynginx/12345
# https://pinetreesquare.com/webtwo/a
# PAUSE THE CLUSTER 
gcloud container clusters resize loadbalancedcluster  --node-pool default-pool --num-nodes 0
#kubectl scale deployment my-mc-deployment --replicas 2
#https://www.youtube.com/watch?v=X48VuDVv0do
#Cleanup
#gcloud init
# DELETE THE CLUSTER
gcloud container clusters delete  cluster-1
# LOOK FOR LOADBALANCERS TO DELETE
