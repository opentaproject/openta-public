(* https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer *)
gcloud init
gcloud container clusters create loadbalancedcluster
kubectl apply -f web-deployment.yaml
kubectl apply -f web-service.yaml
kubectl apply -f basic-ingress-static.yaml 
