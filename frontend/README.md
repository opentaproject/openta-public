This is a [React](https://reactjs.org/) that uses [Vite](https://vitejs.dev/) as a build
environment.

# Install

Make sure you have the following packages / apps isntalled:

* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [Node](https://nodejs.org/en/download/package-manager/)

1. Use the following command to clone the project:

    ```sh
    git clone git@github.com:openta-development/frontend-vite.git
    ```

    This command must be used inside the folder where you want to store the project files.

2. Make sure you are using node --version v18.14.0 
	
	```
	npm --version # v18.14.0
	nvm use 18.14.0
	```
	
3. Start the dev server.  Note that manifest is **not** going to be created. That will be left to collectstatic
    ```
    cd frontend-vite
    nvm use 18.14.0
    git checkout release_v1010 # or whatever matches backend
    npm install --force
    npm audit fix --force
    ```



# Configure the backend

* Set the following  environmental variables

	```
	export BACKEND_HOST=http://v320c.localhost
	USE_VITE=True
	RUNNING_DEVSERVER=True
	```
* Make sure that /etc/hosts has the the corresponding entry mapped to localhost   ie a line with `127.0.0.1	v320c.localhost`

*  build and test the django server

	```
	git checkout release_v1010 # note release matches django-vite
	export USE_CDN=True
	export VERSION=v1000
	python manage.py runserver

	```
* go to `http://v320c.localhost:8000` and make sure things are OK

* start the django devserver to start using VITE
	```
	export USE_CDN=False
	python manage.py runserver --ipv6 "[::1]:8000"
	```

# Running vite in dev mode

* Start the npm dev server

    ```
    export BACKEND_HOST=http://v320c.localhost
    npm run dev
    
    ```
* Go to  [http://localhost:3000/](http://localhost:3000/).

* **Monkeypatch** : go to `http://v320c.localhost:8000` once to populate the cookies

* Use devtools and check the network to make sure vite is loading in dev mode. Empty browswer caches if necessary 

* *If connection failure occurs, double check that you are **not** using the latest npm. Use v18.14.0 vite*

# Use vite in production

* create the vite  build and place the java code in the django dist directory

	```
	export OPENTA_BASEDIR=.... # wherever you placed openta git; no slash at the end
	npm run build
	cp -rp dist $OPENTA_BASEDIR/django/backend
	```
* since `app.css.map` is not created by vite, you may need to monkeypatch dist by adding that file by hand from extra folder. *Waiting for vite to fixe sourcemaps for css files.*

* now using `USE_CDN=False` and `USE_VITE=True` and `DEBUG=True` try using `http://v320c.localhost:8000` and check that java files are served from dist

* now create manifest 
	```
	python manage.py collectstatic
	``` 

