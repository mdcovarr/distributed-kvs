# distributed-kvs
Implementation of a key-value store for Distributed Systems course
CSE 138 at University of California, Santa Cruz (UCSC)

## Information

### Developers
|                               |                               |                               |
| ----------------------------- | ----------------------------- | ----------------------------- |
|**Name:** Michael Covarrubias  |**Name:** Rashmi Chennagiri    |**Name:** Nazib Sorathiya      |
|**CruzID:** mdcovarr           |**CruzID:**  rchennag          |**CruzID:**  nssorath          |
|**Email:** mdcovarr@ucsc.edu   |**Email:**  rchennag@ucsc.edu  |**Email:** nssorath@ucsc.edu   |

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


### Proxy change-view
```
Needs to revceive new view
Needs to create id to shard node
Needs to rehash the keys
Needs to determine which keys it will keep
Needs to send out all other keys
```





## View Change Algorithm
1.
```
  VIEW='10.10.0.4:13800,10.10.0.5:13800'


            +-----------------+              +-----------------+
            |     shard1      |              |     shard2      |
            |     (node1)     |              |     (node2)     |
            | 10.10.0.4:13800 |              | 10.10.0.5:13800 |
            |  ------         |              |  ------         |
            |  - key1         |              |  - key2         |
            |  - key3         |              |  - key4         |
            |  - key5         |              |                 |
            +-----------------+              +-----------------+
```

2. Then there is a view change trigger to **node1**. `http://10.10.0.4:13800/kvs/view-change` to `VIEW=10.10.0.4:13800,10.10.0.5:13800,10.10.0.6:13800`

Hence there is an added node. Node1 needs to tell the rest of the nodes in the current view
that there is a view change. Hence tell **node2**. **Node1** does so by sending **node2**
a `PUT` request via `http://10.10.0.5:13800/proxy/view-change`. `PUT` requests to
`/proxy/view-change` let's other nodes in the view know there is a view change request, and
also let's the nodes know that they were not queried directly by the client.

```


            +-----------------+                                +-----------------+
            |     shard1      |                                |     shard2      |
            |     (node1)     |                                |     (node2)     |
            | 10.10.0.4:13800 |    PUT /proxy/view-change      | 10.10.0.5:13800 |
            |  ------         | --------------------------->   |  ------         |
            |  - key1         |                                |  - key2         |
            |  - key3         |                                |  - key4         |
            |  - key5         |                                |                 |
            +-----------------+                                +-----------------+
```

Once this is complete **every** node in the old view knows there is a view change in place
and they all start to re hash their **own** keys
Hence, node1 will re hash **key1, key3, key5** and node2 re hashes **key2, key4**

3. The re hashing is now done with information of the new view
`VIEW=10.10.0.4:13800,10.10.0.5:13800,10.10.0.6:13800`
given that there are 3 nodes now, the re hashing will be done in order to determine where
a node will distribute it's keys to. (Assuming `node3 = 10.10.0.6:13800`) For example,
node1 will need to re hash it's keys **key1, key3, key5** and determine which keys
will stay locally at node1, and which nodes will be distributed to **node2** and **node3**

Example: thus after node1 finishes re hashing it will come up with some dictionary as such
```
new_distribution = {
  "10.10.0.4:13800": {"key1": "value1"},
  "10.10.0.5:13800": {"key3": "value3"},
  "10.10.0.6:13800": {"key5"}: "value5"}
}
```

Meaning that **key1** will stay on itself (node1), **key3** will be distributed to node2
and **key5** will be distributed to node3 (the newlly added node)

```
             +--------+                             +-------+               +-------+
             | Node 1 |                             | Node2 |               | Node3 |
             +--------+                             +-------+               +-------+
                 |                                     |                         |
                 |                                     |                         |
                 |     PUT /proxy/receive-dict         |                         |
                 |       {"key3": "value3"}            |                         |
                 | ---------------request----------->  |                         |
                 |                                     |                         |
                 |                                     |                         |
                 |     PUT /proxy/receive-dict         |                         |
                 |       {"key5": "value5"}            |                         |
                 | --------------------request---------------------------------> |
                 |                                     |                         |
                 |                                     |                         |
                 |                                     |                         |
                 | <--------------response-----------  |                         |
                 |                                     |                         |
                 |                                     |                         |
                 | <------------------------response---------------------------- |
                 |                                     |                         |
                 |                                     |                         |
                 |                                     |                         |
                 |                                     |                         |
                 |                                     |                         |
                 |                                     |                         |
                 |                                     |                         |
                 v                                     v                         v
```

This same process of re hashing, determining which keys to keep, and what keys to
send to other nodes in the view is also done by all other nodes in the **view**

4. Once this view change is complete we respond to the client. In this case
the client initially sent request to node1. So node1 will respond

```
             +--------+                             +-------+
             | client |                             | Node1 |
             +--------+                             +-------+
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 | <--------------response-----------  |
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 |                                     |
                 v                                     v
```

# Assignment 4
## Replication
Do hashing of each node address with the replication factor

Example
```
VIEW='10.10.0.2:13800,10.10.0.3:13800,10.10.0.4:13800,10.10.0.5:13800'
VIEW=['10.10.0.2:13800' ,'10.10.0.3:13800', '10.10.0.4:13800', '10.10.0.5:13800']
repl-factor = 2

replica = (i % repl_factor) + 1

replicas = {
  '1': ['10.10.0.2:13800', '10.10.0.4:13800'],
  '2': ['10.10.0.3:13800', '10.10.0.5:13800']
}

```

## A node's variables
```
  self.kv_store         // key-value store of the node
  self.view             // View of the current distributed key-value store
  self.ip               // IP of current node
  self.port             // PORT of the current node
  self.address          // IP and PORT of the current node
  self.repl_factor      // Replication Factor
  self.causal_context   // Causal context object
  self.shard_id         // ID of shard the node pertains to
  self.replicas         // replicas also on the same shard
  self.partitions       // all shards and their replicas

  --------------------------------------------------------

  Example: Node 1


  self.kv_store = {}
  self.view = ['10.10.0.2:13800' ,'10.10.0.3:13800', '10.10.0.4:13800', '10.10.0.5:13800']
  self.address = '10.10.0.2:13800'
  self.repl_factor = 2
  self.causal_context = {}
  self.shard_id = 1
  self.replicas = ['10.10.0.2:13800', '10.10.0.4:13800']
  self.partitions = {
      '1': ['10.10.0.2:13800', '10.10.0.4:13800'],
      '2': ['10.10.0.3:13800', '10.10.0.5:13800']
  }
```

# Handle Network Partitions
```
self.causal_context = {
  'key': {
    'TIMESTAMP': 'VALUE'
  }
}

-------------------------

Network Partition

Node 1
self.causal_context = {
  'sampleKey': {
    '1607796868.426495': '10'
  }
}

Node 2
self.causal_context = {
  'sampleKey': {
    '1607796904.313417': '20'
    '1607796904.313419': '3'
    '1607796904.313420': '100'
  }
}

self.causal_context = {
  'sampleKey': {
    'timestamp': 'TIMESTAMP',
    'value': 'VALUE'
  }
}
```


# PUT Changes
```
Node 1 receives PUT /sampleKey

  1. hash 'sampleKey'

  2. sampleKey hashes to Node 1
    2a. Now I check if key is too long
    2b. Check if value existes in JSON

  3. sampleKey didn't have to Node 1 shard, but hashed to Node 3 shard
    3a. Forward request to Node 3
```