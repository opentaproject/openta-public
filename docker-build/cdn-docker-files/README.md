# works on http://opentaproject.com/openta
# TO DEPLOY THIS
export BUCKET_NAME=openta-cdn-bucket
export VERSION_TAG=v2.1.2
gsutil -m cp  install.tgz gs://${BUCKET_NAME}/${VERSION_TAG}

# TO EXECUTE, create GCE according to ../instructions
# then in that image
wget https://storage.googleapis.com/openta-cdn-bucket/v2.1.2/install.tgz
tar xvzf ./install.tgz
docker-compose up
