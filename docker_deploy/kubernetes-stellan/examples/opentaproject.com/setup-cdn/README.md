export PROJECT_NAME=production
export PROJECT_ID=production-304119
export PROJECT_NUMBER=244333042069
export CLUSTER_NAME=openta-prod
export COMPUTE_ZONE=europe-west3-a
export REGION=europe-west3
export BUCKET_NAME=opentaproject-cdn-bucket

# https://cloud.google.com/cdn/docs/setting-up-cdn-with-bucket#gsutil
#export BUCKET_NAME=openta-cdn-bucket
#echo gsutil mb -p ${PROJECT_ID} -c standard -l ${REGION} -b on gs://${BUCKET_NAME}
#echo gsutil cp tennisball.png gs://${BUCKET_NAME}/tennisball.png
#echo gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}
#echo export BUCKET_IP_NAME=${BUCKET_NAME}-ip
#echo gcloud compute addresses create ${BUCKET_IP_NAME} --network-tier=PREMIUM --ip-version=IPV4 --global
#echo export BUCKET_IP=\`gcloud compute addresses describe ${BUCKET_IP_NAME} --format="get(address)" --global\`
#echo $BUCKET_IP
#export BACKEND_NAME=${BUCKET_IP_NAME}-backend
#echo gcloud compute backend-buckets create ${BACKEND_NAME} --gcs-bucket-name=${BUCKET_NAME} --enable-cdn
#echo export URL_MAP=http-lb-openta
#echo gcloud compute url-maps create ${URL_MAP} --default-backend-bucket=${BACKEND_NAME}
#export HTTP_PROXY_NAME=${URL_MAP}-proxy
#echo gcloud compute target-http-proxies create ${HTTP_PROXY_NAME}  --url-map=${URL_MAP}
#echo gcloud compute target-http-proxies describe ${HTTP_PROXY_NAME}  --global
#echo https://storage.cloud.google.com/${BUCKET_NAME}/tennisball.png
#echo gsutil -m cp -r deploystatic gs://${BUCKET_NAME}
#echo gsutil cors set cors.json gs://${BUCKET_NAME}
# ONLY THE APIS LINK TO BUCKET WORKS 
# See https://kevinsimper.medium.com/google-cloud-storage-cors-not-working-after-enabling-14693412e404

gcloud config set project production-304119
gsutil mb -p production-304119 -c standard -l ${REGION} -b on gs://opentaproject-cdn-bucket
gsutil iam ch allUsers:objectViewer gs://opentaproject-cdn-bucket
export BUCKET_IP_NAME=opentaproject-cdn-bucket-ip
gcloud compute addresses create opentaproject-cdn-bucket-ip \
    --network-tier=PREMIUM \
    --ip-version=IPV4 \
    --global
gcloud compute addresses describe  opentaproject-cdn-bucket-ip  \
    --format="get(address)" \
    --global
gsutil cors set cors.json gs://${BUCKET_NAME}
export BUCKET_IP=34.117.57.140
export BACKEND_NAME=${BUCKET_IP_NAME}-backend
export URL_MAP=http-lb-openta
gcloud compute url-maps create http-lb-openta --default-backend-bucket=opentaproject-cdn-bucket-ip-backend
export HTTP_PROXY_NAME=${URL_MAP}-proxy
gcloud compute target-http-proxies create ${HTTP_PROXY_NAME}  --url-map=${URL_MAP}
gcloud compute target-http-proxies describe ${HTTP_PROXY_NAME}  --global
gsutil cp tennisball.png gs://${BUCKET_NAME}/tennisball.png
# NOW CHECK THAT TENNISBALL IS AVAILABLE 
echo https://storage.cloud.google.com/${BUCKET_NAME}/tennisball.png
# COMMAND FOR UPLOADING FILES
echo gsutil -m cp -r deploystatic gs://${BUCKET_NAME}
