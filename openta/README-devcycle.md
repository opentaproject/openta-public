# WARNING THIS ASSUMES THE GLOBAL $VERSION IS PROPERLY SET FOR THE VERSION YOU WANT

cd frontend
brunch build
cd ../django/backend
source ../env-alpha/bin/activate
python manage.py collectstatic
cd backend
cp settings.py settings_production_kubernetes.py
cp settings.py settings_production_docker.py
cd ..
source ./install_frontend
# test the cdn image by commenting out the STATIC_URL in the RUNNING_DEV_SERVER test
# run devserver and replace the comment when done
#
# make sure openta-base:${VERSION} is uptodate
# check out docker-openta/openta-base
# and if necessary 
cd docker-openta/openta-base ; source ./install
# this is only neccessary for updates to the requirements file
# make sure openta-nginx:${VERSION} is uptodate
cd docker-openta/openta-nginx ; source ./install 
# Note that nginx.conf is ignored; there is a persistent volume version on the server
# which was useful for debugging and should be the same as that openta-nginx

# finally from project base
source ./install

