docker build --tag ${DOCKER_REPO}/openta:${VERSION_TAG}  .
docker push ${DOCKER_REPO}/openta:${VERSION_TAG} 
