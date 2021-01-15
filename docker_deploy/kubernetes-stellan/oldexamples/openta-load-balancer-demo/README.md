(* https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer *)
gcloud init
# GET A STATIC IP
#gcloud compute addresses create pts-address --global
#gcloud compute addresses describe pts-address --global
# SET UP DNS AND WAIT UNTIL ADDRESS IS RESOLVED VIA PING
docker login
gcloud container clusters create loadbalancedcluster --num-nodes=2 --machine-type=e2-standard-2 
#kubectl apply -f loadbalancedcluster/my-mc-certificate-1.yaml
#kubectl describe managedcertificate my-mc-certificate-1
#kubectl scale deployment loadbalancedcluster  --replicas 6
kubectl create secret docker-registry dockerkey --docker-server=https://index.docker.io/v1/  \
	--docker-username=s53ostlund --docker-password=E95ostlund --docker-email=stellan.ostlund@gmail.com
gcloud container clusters get-credentials loadbalancedcluster  --zone europe-north1-b --project demoproject-296306
kubectl create clusterrolebinding cluster-admin-binding   --clusterrole cluster-admin   --user $(gcloud config get-value account)
# https://cloud.google.com/community/tutorials/nginx-ingress-gke
# https://diwaker.io/howto-cert-manager-with-ingress-nginx-on-gke/
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install basic-ingress ingress-nginx/ingress-nginx \
	--set controller.service.loadBalancerIP=130.211.32.53 \
	--set rbac.create=true 

kubectl apply -f loadbalancedcluster 
kubectl --namespace default get services -o wide -w basic-ingress-ingress-nginx-controller
k describe ingress basic-ingress 
kubectl patch svc basic-ingress-ingress-nginx-controller  -p '{"spec": {"loadBalancerIP": "130.211.32.53"}}'

https://stackoverflow.com/questions/41459592/global-static-ip-name-on-nginx-ingress
kubectl scale deployment loadbalancedcluster  --replicas 6
gcloud container clusters resize loadbalancedcluster --node-pool default-pool --num-nodes 0
#helm install --name nginx-ingress stable/nginx-ingress \
#      --set controller.service.loadBalancerIP=<YOUR_EXTERNAL_IP> 

# https://diwaker.io/howto-cert-manager-with-ingress-nginx-on-gke/
helm install basic-ingress ingress-nginx/ingress-nginx \
	--set controller.service.loadBalancerIP=<YOUR_EXTERNAL_IP> 
	

# GO TO http://35.228.62.133.xio.io
# SELF_SIGNED: 
# GO TO https://35.228.62.133.xio.io 

# https://www.youtube.com/watch?v=X48VuDVv0do
# k exect -it v212b-XXXXX -c web -- /bin/bash
# manage.py ....
#kubectl apply -f web-deployment.yaml
#kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.43.0/deploy/static/provider/cloud/deploy.yaml
#kubectl apply -f web-service.yaml
#kubectl apply -f basic-ingress-static.yaml 
# https://www.codegravity.com/blog/kubernetes-ingress-nginx-path-forwarding-does-not-work
# #https://kubernetes.github.io/ingress-nginx/user-guide/basic-usage/
# https://cloud.google.com/community/tutorials/nginx-ingress-gke 
# https://github.com/kubernetes/ingress-nginx/issues/1120
#k apply -f loadbalancer/
# https://kubernetes.github.io/ingress-nginx/deploy/
#kubectl create clusterrolebinding cluster-admin-binding   --clusterrole cluster-admin   --user $(gcloud config get-value account)
#helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
#helm repo update
#helm install basic-ingress ingress-nginx/ingress-nginx

#kubectl --namespace default get services -o wide -w basic-ingress-ingress-nginx-controller
# NOTE EXTERNAL IP
curl ..... 

# AFTER HELM INSTALL

An example Ingress that makes use of the controller:

  apiVersion: networking.k8s.io/v1beta1
  kind: Ingress
  metadata:
    annotations:
      kubernetes.io/ingress.class: nginx
    name: example
    namespace: foo
  spec:
    rules:
      - host: www.example.com
        http:
          paths:
            - backend:
                serviceName: exampleService
                servicePort: 80
              path: /
    # This section is only required if TLS is to be enabled for the Ingress
    tls:
        - hosts:
            - www.example.com
          secretName: example-tls

If TLS is enabled for the Ingress, a Secret containing the certificate and key must also be provided:

  apiVersion: v1
  kind: Secret
  metadata:
    name: example-tls
    namespace: foo
  data:
    tls.crt: <base64 encoded cert>
    tls.key: <base64 encoded key>
  type: kubernetes.io/tls

