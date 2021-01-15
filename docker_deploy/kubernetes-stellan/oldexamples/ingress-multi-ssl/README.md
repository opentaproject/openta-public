gcloud init
gcloud container clusters create cluster-1 --zone europe-north1-b --node-locations europe-north1-b --num-nodes=2  --machine-type=e2-standard-2 
kubectl create secret docker-registry dockerkey --docker-server=https://index.docker.io/v1/  --docker-username=XXXXX  --docker-password=XXXXX  --docker-email=stellan.ostlund@gmail.com
gcloud container clusters get-credentials cluster-1 --zone europe-north1-b --project demoproject-296306
#kubectl scale deployment my-mc-deployment --replicas  1
# THE mynginx service only echoes the uri
# create it by building the docker file in nginx directory
# DO  THE FOLLOWING ONLY ONCE to create a named IP address
gcloud compute addresses create pts-address --global
# 
gcloud compute addresses describe pts-address --global
kubectl apply -f yamls
kubectl describe managedcertificate my-mc-certificate-1
kubectl describe ingress my-mc-ingress 
kubectl describe managedcertificate my-mc-certificate-1
# TAKES ABOUT 8-25 MINUTES TO PROVISION AND MAKE VISIBLE
# IN THE MEANTIME http may work and https gives failueres
# EVEN AFTER curl works, webpage may fail for another few minutes
# https://v2.pinetreesquare.com
# https://pinetreesquare.com/mynginx/12345
# https://pinetreesquare.com/webtwo/a
# PAUSE THE CLUSTER 
gcloud container clusters resize cluster-1  --node-pool default-pool --num-nodes 0
#kubectl scale deployment my-mc-deployment --replicas 2
#https://www.youtube.com/watch?v=X48VuDVv0do
#Cleanup
#gcloud init
# DELETE THE CLUSTER
gcloud container clusters delete  cluster-1
# LOOK FOR LOADBALANCERS TO DELETE
