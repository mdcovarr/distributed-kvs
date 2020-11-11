# distributed-kvs
Implementation of a key-value store for Distributed Systems course
CSE 138 at University of California, Santa Cruz (UCSC)

## Information
**Name:** Michael Covarrubias

**CruzID:** mdcovarr

**Email:** mdcovarr@ucsc.edu

# Grab Repository
1. Open terminal
2. `cd` into whatever folder you want to put the repository in ex: `~/Projects`
3. `git clone git@github.com:mdcovarr/distributed-kvs.git`

## Setup Virtual Environment
1. `cd distributed-kvs/`
2. `python3 -m venv --system-site-packages ./venv` this will create a directory `distributed-kvs/venv` which
contains the python, pip and packages for your virtual environment
3. Now activate your virtual environment with command `source ./venv/bin/activate`
4. Install python packages required for backend software with command `pip install -r requirements.txt`

## Software Requirements
```
python >= 3.8
pip >= 19.2

docker >= 19 (if you want to deploy docker container of project)
```

Also, you need to install all python requirements for your application to
run successfully.

At root directory of repository, run command:
```
pip install -r requirements.txt
```

# Repository Structure
```
./
├── Dockerfile
├── README.md
├── distributed_kvs
│   ├── __init__.py
│   ├── app.py
│   ├── main_app.py
│   ├── myconstants.py
│   └── proxy_app.py
├── requirements.txt
└── tests
    └── test_assignment2.py

```

# Run Software
1. Open terminal
2. `cd distributed-kvs`
3. Make sure you are in your virtual enviornment `source ./venv/bin/activate`
4. Run: `python distributed_kvs/app.py`
5. NOTE: currently by default `IP = 0.0.0.0` and `PORT = 13800`

Output will look similar to below:
```
(venv) michael@MacBook-Pro distributed-kvs % python distributed_kvs/app.py
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:13800/ (Press CTRL+C to quit)
```