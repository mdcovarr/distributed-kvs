# distributed-kvs
Implementation of a key-value store for Distributed Systems course
CSE 138 at University of California, Santa Cruz (UCSC)

## Information

### Developers
|                               |                               |                               |
| ----------------------------- | ----------------------------- | ----------------------------- |
|**Name:** Michael Covarrubias  |**Name:** Rashmi Chennagiri    |**Name:** Nazib Sorathiya      |
|**CruzID:** mdcovarr           |**CruzID:**                    |**CruzID:**                    |
|**Email:** mdcovarr@ucsc.edu   |**Email:**                     |**Email:**                     |

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
│   ├── proxy_app.py
│   └── shard_node.py
├── requirements.txt
├── test_assignment3.sh
└── tests
    ├── test_assignment2.py
    ├── test_assignment3.py
    └── test_assignment3_test2.py

2 directories, 13 files
```

### Help on running application
Run command `python distributed_kvs/app.py -h` to get help on running application

Output will look similar to:
```
(venv) michael@MacBook-Pro distributed-kvs % python distributed_kvs/app.py -h
usage: app.py [-h] [-i IP] [-p PORT]

Application implementing a distributed Key-Value Store

optional arguments:
  -h, --help            show this help message and exit
  -i IP, --ip IP        IP Address to use for client to connect to, or server to listen on. Value defaults to 0.0.0.0 if no argument provided
  -p PORT, --port PORT  Port for server to listen on. value defaults to 13800 if no argument provided
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