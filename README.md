# rpx

## Objective

This project contains the implementation of the reverse proxy component
of a multi-tier application whose archutecture is shown below

<img src="https://github.com/gmateesc/rpx/tree/images/arch.png" alt="sys arch" width="400">

The reveres proxy sits between multiple clients and one or several
instances of a downstream service.

- The reverse proxy supports multiple downstream services with multiple
instances

- Downstream services are identified using the Host Http header.


The reverse proxy implement sthe following flow:

- It listens to HTTP requests and forwards them to one of the instances
  of a downstream service that will process the requests.

- Requests are load-balanced and should support multiple loadbalancing
  strategies.

- After processing the request, the downstream service sends the HTTP
  response back to the reverse proxy.



## Configuration

```yaml

proxy:

  listen:
    address: "0.0.0.0"
    port: 8080

  services:
  - name: my-service
    domain: my-service.my-company.com
    hosts:
    - address: "127.0.0.1"
      port: 9090
    - address: "127.0.0.1"
      port: 9091

  # Supported load balancing algorithms
  #  round-robin
  #  random
  load_balancing:
    algorithm: round-robin
```
