JC
## Architecture: Microservices (Payment + Stock + Order)

## Framework: Flask + Redis on Kubernetes

- ##### SAGA Pattern for transactions (compensating transactions)

### Evaluation:

- Scalability (10k+ requests per second)
- Consistency
  - use **two phase lock** and **idempotency key**
- Performance (throughput latency)
- Fault Tolerance
- Availability



Useful links: 

- https://www.youtube.com/watch?v=JmCn7k0PlV4
- https://www.youtube.com/watch?v=OqCK95AS-YE
- https://www.youtube.com/watch?v=X48VuDVv0do&t=263s





# Web-scale Data Management Project Template

Basic project structure with Python's Flask and Redis. 
**You are free to use any web framework in any language and any database you like for this project.**

### Project structure

* `env`
  Folder containing the Redis env variables for the docker-compose deployment

* `helm-config` 
  Helm chart values for Redis and ingress-nginx

* `k8s`
  Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.

* `order`
  Folder containing the order application logic and dockerfile. 

* `payment`
  Folder containing the payment application logic and dockerfile. 

* `stock`
  Folder containing the stock application logic and dockerfile. 

* `test`
  Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

### Deployment types:

#### docker-compose (local development)

After coding the REST endpoint logic run `docker-compose up --build` in the base folder to test if your logic is correct
(you can use the provided tests in the `\test` folder and change them as you wish). 

***Requirements:*** You need to have docker and docker-compose installed on your machine.

#### minikube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud. 
First deploy your database using helm by running the `deploy-charts-minicube.sh` file (in this example the DB is Redis 
but you can find any database you want in https://artifacthub.io/ and adapt the script). Then adapt the k8s configuration files in the
`\k8s` folder to mach your system and then run `kubectl apply -f .` in the k8s folder. 

***Requirements:*** You need to have minikube (with ingress enabled) and helm installed on your machine.

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster. 

***Requirements:*** You need to have access to kubectl of a k8s cluster.





# Testing Instructions

## Setup 

* Install python 3.8 or greater (tested with 3.11)
* Install the required packages using: `pip install -r requirements_stress.txt`
* Change the URLs and ports in the `urls.json` file with your own

````
Note: For Windows users you might also need to install pywin32
````

## Stress Test

In the provided stress test we have created 6 scenarios:

1) A stock admin creates an item and adds stock to it

2) A user checks out an order with one item inside that an admin has added stock to before

3) A user checks out an order with two items inside that an admin has added stock to before

4) A user adds an item to an order, regrets it and removes it and then adds it back and checks out

5) Scenario that is supposed to fail because the second item does not have enough stock

6) Scenario that is supposed to fail because the user does not have enough credit

To change the weight (task frequency) of the provided scenarios you can change the weights in the `tasks` definition (line 358)
With our locust file each user will make one request between 1 and 15 seconds (you can change that in line 356).

```
YOU CAN ALSO CREATE YOUR OWN SCENARIOS AS YOU LIKE
```

### Running

* Open terminal and navigate to the `locustfile.py` folder
* Run script: `locust -f locustfile.py --host="localhost"`
* Go to `http://localhost:8089/`


### Stress Test Kubernetes 

The tasks are the same as the `stress-test` and can be found in `stress-test-k8s/docker-image/locust-tasks`.
This folder is adapted from Google's [Distributed load testing using Google Kubernetes Engine](https://cloud.google.com/architecture/distributed-load-testing-using-gke)
and original repo is [here](https://github.com/GoogleCloudPlatform/distributed-load-testing-using-kubernetes). 
Detailed instructions are in Google's blog post.
If you want to deploy locally or with a different cloud provider the lines that you have to change are:
1) In `stress-test-k8s/kubernetes-config/locust-master-controller.yaml` line 34 you could add a dockerHub image that you
published yourself and in line 39 set `TARGET_HOST` to the IP of your API gateway. 
2) Change the same configuration parameters in the `stress-test-k8s/kubernetes-config/locust-worker-controller.yaml`


### Using the Locust UI

Fill in an appropriate number of users that you want to test with. 
The hatch rate is how many users will spawn per second 
(locust suggests that you should use less than 100 in local mode). 


## Consistency Test

In the provided consistency test we first populate the databases with 100 items with 1 stock that costs 1 credit 
and 1000 users that have 1 credit. 

Then we concurrently send 1000 checkouts of 1 item with random user/item combinations.
If everything goes well only 10% of the checkouts will succeed, and the expected state should be 0 stock across all 
items and 100 credits subtracted across different users.  

Finally, the measurements are done in two phases:
1) Using logs to see whether the service sent the correct message to the clients
2) Querying the database to see if the actual state remained consistent

### Running

* Run script `run_consistency_test.py`

### Interpreting Results

Wait for the script to finish and check how many inconsistencies you have in both the payment and stock services
