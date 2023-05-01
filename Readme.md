## Architecture: Microservices



## Framework: Flask + Redis + Kubernetes



### Evaluation:

- Scalability (10k+ requests per second)
- Consistency
  - use **two phase lock** and **idempotency key**
- Performance (throughput latency)
- Fault Tolerance
- Availability



#### SAGA Pattern for transactions

