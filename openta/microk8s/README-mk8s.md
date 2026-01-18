# Setting up a mikrok8s cluster for openta. 

  ```sudo microk8s refresh-certs --cert server.crt```

## Set up an ubuntu 24.04 instance and install nginx and letsencrypt and wildcard certificates.

- make sure you have a domain and access to the dns records
- install nginx
```sudo apt install nginx nginx-common nginx-core```

- Make sure you get the nginx welcome on your vps http://example.com

### Set up encryption
- Either method ; letsencrypt is probably most secure but certificate needs renewal every three months
- cloudflare enables certificates that last 15 years but you need to give it decryptions priviledges

#### Option 1: Use cloudflare
- Sign up for cloudflare or open your account and subscribe your example.com site and enable your domain
- Copy the dns assigned by cloudflare
- Make sure your A records are proxied
- Now wait until cloudflare no longer is flagging invalid  nameserver; this might take 30 minutes
- Create an origin certificate at cloudflares and copy them to the following locations and restart nginx
```
 listen [::]:443 ssl ipv6only=on; # 
 listen 443 ssl; # managed by Certbot
 ssl_certificate /etc/cloudflare/cert.pem;
 ssl_certificate_key /etc/cloudflare/privkey.pem;
```
- restart the nginx server
  - `sudo systemctl restart nginx`
- make sure that ```https://example.com``` is working


#### Option 2: Use letsencrypt
- install certbot
```sudo snap install --classic certbot ``` 
- Now fix the server_name in ```/etc/nginx/sites-enabled/default``` to be
``` server_name example.com *.example.com;```
- reload nginx
    - ```sudo systemctl reload nginx```
- check nginx is working using `curl http://localhost`
- Make sure you can get nginx welcome from outside on port 80. Use `curl -k -v http://example.com` 
- Create A records for `*.example.com` and `example.com`  at the DNS provider
- Install wildcard certificate so you can reach domains ```*.example.com```
  -  `sudo certbot certonly --manual --preferred-challenges=dns --email me@example.com --server https://acme-v02.api.letsencrypt.org/directory --agree-tos -d example.com -d *.example.com`
  -  Create the TXT records for the DNS at your DNS provider that has the text from the certbot command.  
  -  *Remember to allow the TXT record to propagate so you don't get locked out of your domain.* 
  -  You can check if the TXT records have propagated by looking for `_acme-challenge.example.com`
- Now make sure that you can access `https://anything.example.com` from external IP's and that your get the nginx welcome 
- now locate  the files `cert.pem` and `privkey.pem` in `/etc/letsencrypt/archive/example.com` 
- `sudo certbot certificates` can be  helpful
- restart the nginx server
  - `sudo systemctl restart nginx`

#### Install mikrok8s
For convenience add the following to your .bashrc
```
alias kubectl="microk8s kubectl"
alias k="microk8s kubectl"
export SERVER_NAME=changeme
```
Logout and back in again to get alias working. 

- set machine name
  - ```sudo hostnamectl set-hostname ${HOST_NAME}```
  - ```sudo echo "127.0.1.1 ${HOST_NAME}" >> /etc/hosts```

- install mikrok8s 
  - ```sudo snap install microk8s --classic --channel=1.30```
  - ```sudo usermod -a -G microk8s $USER ```
  - ```mkdir -p ~/.kube ```
  - ```chmod 0700 ~/.kube ```
  - ```su - $USER```
  - ```microk8s status --wait-ready```
  - ```microk8s enable ingress```
  - ```microk8s enable hostpath-storage ```
  - ```microk8s enable dns```
  - ```# microk8s enable cert-manager # skip if using cloudflare ```
  - ```microk8s enable registry```

Be careful to renew certs; when they expire the whole site stops working completely and kubectl stops working

``` 
 sudo sh -c '
 for c in /var/snap/microk8s/current/certs/*.crt; do
    echo "=== $(basename "$c") ==="
    openssl x509 -in "$c" -noout -enddate
  done
 '
 ```

- To renew, run 
 ```sudo microk8s refresh-certs --cert server.crt```

### Now run a simple test server in microk8s 

- Install the wildcard certificates as secret
  - ```kubectl create secret tls openta-tls-secret --key privkey.pem  --cert cert.pem```
    -  Delete local copies of the `.pem` 

- Install basics
  - ```export HOST_NAME=example.com  #your FQDM hostname```
  - ```sudo mkdir -p /mnt/pv/subdomain-vol```
  - ```sudo mkdir -p /mnt/pv/deploystatic-vol```
  - ```sudo mkdir -p /mnt/pv/minikube-vol```
  - ```sudo chmod -R 0757 /mnt/pv ```
  - ```k apply -f 0-storage-class.yaml```
  - ```envsubst < 0-persistent-volumes.yaml | k apply -f - ```
  - ```envsubst < 1-test-nginx.yaml | k apply -f -``` 

On the host, make sure that the file `/mnt/pv/subdomain-vol/index.html` is present
Now exec  the nginx pod and make sure /subdomain-data exists and that the file index.html is present

Now try the web address  from the internet 
  - https://abc.example.com
  - https://anything.example.com

**Until this works there is no  point in continuing**

#### Clean up
```
sudo rm /mnt/pv/subdomain-vol/index.html
k delete -f 1-test-nginx.yaml 
```
### Install more components

#### Prepare environment variables
Create a `.envrc` file with the following variables: 
```
export SUPERUSER_PASSWORD=changeme
export POSTGRES_DEFAULT_DB=changeme # default postgres
export PGPASSWORD=changeme          
export PGUSER=changeme              # default postgres
export SECRET_KEY=changeme
export DJANGO_SECRETS_FILE=stub
export DOMAIN_NAME=example.com # your FQDN
export SERVER_NAME=example # suggestion to just keep basename
```

Replace `changeme` with suitable values; replace myfqdname by your fully qualified domain name

Load the `.envrc` settings into your current shell. Either automatically or using the commands below.

```bash
set -a; source .envrc; set +a
```



Install database server
```
envsubst <  5-dbserver.yaml | k apply -f -
```
Now exec into the database server and set up databases and owners; note that environmental variable names may be renamed in the db-server app. Exec into the postgres app 

```
k exec -it db-server -- /bin/bash
```
Perform the following commands
```
psql -U ${POSTGRES_USER} -c "CREATE DATABASE opentadefault1 OWNER ${POSTGRES_USER};"
psql -U ${POSTGRES_USER} -c "CREATE DATABASE sites OWNER ${POSTGRES_USER};"
psql -U ${POSTGRES_USER} -c "CREATE DATABASE opentasites OWNER ${POSTGRES_USER};"
```
#### Now set up the rest of the containers
```
k apply -f 7-redis.yaml
k apply -f 9-memcached.yaml
```
Check services; db-server, memcached and redis should be running:
```
k get pods
k get svc
```
Finally apply the yaml for openta
```
envsubst <  openta.yaml  | k apply -f -
```


### Instructions for first time install  of openta
```
# create-docker-secret ## ONLY IF YOU ARE GOING TO BE PULLING FROM RESTRICTED REPO
k exec -it openta -- /bin/bash
python manage.py createcachetable
python manage.py migrate
```
Now try creating a blank course
```
./python py_createcourse test1 

```
test https://test1.example.com/


#### Set up pgbouncer if you want to use it. Only for production.
exec into db-server
```
k exect -it db-server -- /bin/bash
```
Check encryption scheme
```
psql -U ${POSTGRES_USER} -c "SHOW password_encryption;"
```
It should show ```scram-sha-256```. Assuming it does, extract the scram hash
```
psql -U ${POSTGRES_USER} -c "SELECT rolpassword FROM pg_authid WHERE rolname = '${POSTGRES_USER}'";
```
copy the entire hash including the identifer ```SCRAM=SHA-256xxx``` into the clipboard  and add the ```export SCRAM_PASSWORD='SCRAM=SHA-256xxx'```  into your .envrc. Do not miss the single quotes to make sure that  special characters are not lost. 

Now you can install pgbouncer
```
envsubst -f < 6-pgbouncer.yaml | k apply -f -
```
In order to user pgbouncer, enable ot om the file openta.yaml.

Change environmental variables to enable it
```
  -name: NOT_PGHOST
   value: db-server
  -name: PGHOST
   value: pgbouncer-service
```
