# Indiana Bar Foundation - Mock Trial Scheduler Backend

This project allows to run a quick application with ReactJS (Javascript front-end), Flask (Python backend) and PostgreSQL (relational database) by running it on Docker containers.

### Features

A database named `sport_stats` (user: myuser / password: mypassword) is initialized when the database container start. These default values can be changed in the `docker-compose.yml` file.
A table `players` with one record is created by copying the file `db/init/init.sql` into the `/docker-entrypoint-initdb.d/` container directory ([see documentation of postgres official image](https://hub.docker.com/_/postgres/)).

The Flask application uses SQLAlchemy to retrieve the content of the `players`, ReactJS call the REST API and display it !

**Hot reloading** is enabled for the React and Flask code, after every code change the container is up-to-date automatically !

### Run the app (React Front-End)

Everything is containerized from the client, backend to the database. So all you need is Docker installed, and then you can run :

```
docker-compose up --build
```

And your app will be up on the *port 3000* !

Alternatively, to bypass the usage of Docker, navigate to the /client/ folder and run :

```
npm start
```

Any non-critical npm vulnerabilities can be ignored without apparent issue. Fix critical vulnerabilities with : 

```
npm audit fix
```

Add the following command in your client/package.json file, to link the frontend and backend.
The frontend uses port 3000, while the backend uses 5000. This tells react to send requests
to port 5000 (ports might differ per user).

```angular2html
"proxy": "http://localhost:5000"
```

### Run the app (Flask Back-End)

Create a python virtual environment in the root of the application. I named mine "test" for testing

Windows:
```
virtualenv -p python3 test
```
A folder named test is then created

Activate the environment by navigating to /test/Scripts/ and running :

```
./activate
```

Activation is confirmed by the word (test) on the very left of your terminal

Make sure the environmental variable FLASK_APP is set to /backend/api/api.py

Windows:
```
$env:FLASK_APP="api.py"
```

Make sure flask is set to debug mode

Windows:
```
$env:FLASK_ENV = "development"
```

From within the /backend/api folder, run :

```
flask run
```

Expected output of above code snippet :

```
 * Tip: There are .env or .flaskenv files present. Do "pip install python-dotenv" to use them.
 * Serving Flask app 'api.py' (lazy loading)
 * Environment: development
 * Debug mode: on
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
 * Restarting with stat
 * Tip: There are .env or .flaskenv files present. Do "pip install python-dotenv" to use them.
 * Debugger is active!
 * Debugger PIN: 733-823-217
```


### Special notes

##### Using Docker Toolbox

This project was implemented with [Docker Toolbox](https://docs.docker.com/toolbox/toolbox_install_windows/), which need some fixes ([read my article on medium for more information](https://medium.com/@thimblot/using-docker-on-windows-without-hyper-v-troubleshooting-tips-2949587f796a)) before running the `docker-compose up` command.
That's the goal of the `docker-compose-up.sh` file at the root of the project, use it instead of the `docker-compose up` command if you are running Docker with the Toolbox.

Flask and ReactJS part of the application use the IP adress / port for containers communication (see `config.py` and `config.js`). You can normally use the name of the service located on the docker-compose.yml, but it doesn't seems to work using Docker Toolbox !

##### Reloading Database configuration

If you change user, password, database name or any other kind of database configuration, you may need to run `docker-compose -up --build` from a fresh start. Make sure to run `docker-compose down` before or even `docker-compose rm` if some containers are stopped but not destroyed.
