# rpx

## Objective

This project contains the implementation of the reverse proxy component
of a multi-tier application whose archutecture is shown below

<img src="https://github.com/gmateesc/rpx/blob/main/images/arch.png" alt="sys arch" width="650">

The reveres proxy is located between multiple clients and one or more instances
of a downstream service.

- The reverse proxy supports multiple downstream services with multiple
  instances;

- Downstream services are identified using the Host Http header.


The reverse proxy implements the following flow:

- It listens to HTTP requests and forwards them to one of the instances
  of a downstream service that will process the requests.

- Requests are load-balanced and should support multiple loadbalancing
  strategies.

- After processing the request, the downstream service sends the HTTP
  response back to the reverse proxy.



## Solution implementation


The reverse proxy is implemented by the python module reverse_proxy.py,
which contains the routing logic and uses the app package containg
the confg and util modules:

```bash
$ tree src/
src/
├── app
│   ├── __init__.py
│   ├── config.py
│   └── util.py
├── config
│   └── reverse_proxy.yaml
└── reverse_proxy.py
```


The config module processes the reverse proxy configuration file,
as described next.


## Configuration

The porxy configuration file processed by the config module is determined as follows:
- if the configuration file /etc/rpx/reverse_proxy.yaml is present, then it is used;
- otherwise, the default configuration file config/reverse_proxy.yaml is used,
whose contents is shown below:

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

In a real application the default settings are not suitable
(for example, the setting proxy.services[0].hosts[0].adress
likely needs to be chaned.)


To suuport deploy-time coniguration of the reverse proxy,
Kubernetes configMap resource is used, whose content is
provided to the reverse proxy application using a volume
specifed in the deployment descriptor.


## Load balancing

The downstream service(s) served by the proxy can contain multiple instances.
The reverse proxy supports two load balancing algorithms:

- round-robin;

- random

The optional proxy.load_balancing parameter in the config file defines
the load balancing algorithm. If this parameter is not present, then
by default round-robin balancing is used.

