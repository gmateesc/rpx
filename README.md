# RPX


## https://github.com/gmateesc/rpx/blob/main/README.md#kubernetes-resources-created


## Table of Contents

- [Objective](#objective)

- [Solution implementation](#solution)

- [Configuration](#config)

- [Load balancing](#lb)


- [Deployment to Kubernetes](#deploy2k8s)
  - [The Kubernetes resources created](#k8s-rsrc)
  - [Downstream service instances](#downstream-svc)
  - [Create config-map resource](#configmap)
  - Deployment of the application(#deploy-app)



<a name="objective" id="objective"></a>
## Objective

This project contains the implementation of the reverse proxy component
of a multi-tier application whose archutecture is shown below

<img src="https://github.com/gmateesc/rpx/blob/main/images/arch.png" alt="sys arch" width="720">

The reveres proxy is located between multiple clients and one or more instances
of a downstream service.

The reverse proxy provides the following features:

- it supports HTTP version is 1.1 and messages encoded in JSON;

- it supports multiple downstream services with multiple instances;

- downstream services are identified using the Host Http header.



The reverse proxy implements the following flow:

- It listens to HTTP requests and forwards them to one of the instances
  of a downstream service that will process the requests.

- Requests are load-balanced and should support multiple loadbalancing
  strategies.

- After processing the request, the downstream service sends the HTTP
  response back to the reverse proxy.

- The reverse proxy forwards the response to the client making
  the initial request.



<a name="solution" id="solution"></a>
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



<a name="config" id="config"></a>
## Configuration

The proxy configuration file processed by the config module is determined as follows:

- if the configuration file */etc/rpx/reverse_proxy.yaml* is present, then it is used;

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


<a name="lb" id="lb"></a>
## Load balancing

The downstream service(s) served by the proxy can contain multiple instances.
The reverse proxy supports two load balancing algorithms:

- round-robin;

- random


The optional proxy.load_balancing parameter in the config file defines
the load balancing algorithm. If this parameter is not present, then
by default round-robin balancing is used.



<a name="deploy2k8s" id="deploy2k8s"></a>
## Deployment to Kubernetes


<a name="k8s-rsrc" id="k8s-rsrc"></a>
### The Kubernetes resources created


Deployment to Kubernetes is done using two configuration files:

```bash
$ tree deploy
deploy
├── reverse-proxy-application.yaml
└── reverse-proxy-configmap.yaml
```

These two files contain the followin specifications:

- *reverse-proxy-configmap.yaml* defines the config-map
  the contains the reverse configuration to be injected
  into the reverse proxy pod;

- *reverse-proxy-application.yaml* defines the Kuberners
  deployment and service resources that provide the
  the reverse proxy application, having a persistent IP address.

The config-map resource definition includes the IP address
and port of the instance(s) of the downstream services, and
it is used to inject in the reverse proxy the system configuration
*/etc/rpx/reverse_proxy.yaml*.


Next section de onstrate a full deployment example.



<a name="downstream-svc" id="downstream-svc"></a>
### Downstream service instances

For the sake of simplicity, assume there is one downstream service with two
instances. A simple way to create a demo downstream is to use NGINX
(the default NGINX deployment proovides HTML rather than JSON content,
so in this case the JSON capability of the reverse proxy is not tested).

The first service instance can be created as follows:
```bash
  k8s-master $ kubectl create deployment nginx1 --image=nginx
  deployment.apps/nginx1 created

  k8s-master $ kubectl create service nodeport nginx1 --tcp=9090:80
  service/nginx1 created

  k8s-master $ kubectl describe service nginx1 | egrep ^IP:
  IP:                       10.97.135.24

  k8s-master $ curl -isS 10.97.135.24:9090 | head -2
  HTTP/1.1 200 OK
  Server: nginx/1.19.6
```

Similarly, the second service instance can be created as follows:
```bash
  k8s-master $ kubectl create deployment nginx2 --image=nginx
  deployment.apps/nginx2 created

  k8s-master $ kubectl create service nodeport nginx2 --tcp=9091:80
  service/nginx2 created

  k8s-master $ kubectl describe service nginx2 | egrep ^IP:
  IP:                       10.108.74.161

  k8s-master $ curl -isS 10.108.74.161:9091 | head -2
  HTTP/1.1 200 OK
  Server: nginx/1.19.6
```


At this point, we know the IP address and port of the two instances of
the downstream service:
- 10.97.135.24:9090
- 10.108.74.161:9091

Next, we use this information to create the config-map resource.



<a name="configmap" id="configmap"></a>
### Create config-map resource

Now we creat the config-map resource, which we will inject into the
reverse-proxy pod under /etc/rpx/reverse_proxy.yaml in order to override 
the default configuration provided under config/reverse_proxy.yaml

We use the information obtained at the previous step to define
the config map resource using specification provided by the
*reverse-proxy-configmap.yaml* file:

```yaml
$ cat reverse-proxy-configmap.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: reverse-proxy-configmap
  namespace: default
data:
  reverse_proxy.yaml: |
    proxy:
      listen:
        address: 0.0.0.0
        port: 8080
      services:
      - name: my-service
        domain: my-service.my-company.com
        hosts:
        - address: 10.97.135.24
          port: 9090
        - address: 10.108.74.161
          port: 9091      
      # Supported load balancing algorithms
      #  round-robin
      #  random
      load_balancing:
        algorithm: round-robin
```


Now we create the config-map resource using the *reverse-proxy-configmap.yaml* file:

``` bash
  $ kubectl apply -f reverse-proxy-configmap.yaml
  configmap/reverse-proxy-configmap created

  $ kubectl get  configmap/reverse-proxy-configmap -o yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: reverse-proxy-configmap
    namespace: default
    uid: 8b8d5c42-174f-4a64-be1e-e3c09ba09b65
  data:
    reverse_proxy.yaml: "proxy:\n  listen:\n    address: 0.0.0.0\n    port: 8080\n  services:\n
      \ - name: my-service\n    domain: my-service.my-company.com\n    hosts:\n    -
      address: 10.97.135.24\n      port: 9090\n    - address: 10.108.74.161\n      port:
      9091      \n  # Supported load balancing algorithms\n  #  round-robin\n  #  random\n
      \ load_balancing:\n    algorithm: round-robin\n"
```



<a name="deploy-app" id="deploy-app"></a>
### Deployment of the application

Now we are ready to deploy the application; we create a deployment,
containing two pods and expose the application as a service with a
persistent IP address using the specification contained in the
*reverse-proxy-application.yaml* file

$ cat reverse-proxy-application.yaml 