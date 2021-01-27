# RPX


## Table of Contents

- [Objective](#objective)

- [Solution implementation](#solution)

- [Configuration](#config)

- [Load balancing](#lb)

- [Deployment to Kubernetes](#deploy2k8s)
  - [The Kubernetes resources created](#k8s-rsrc)
  - [Downstream service instances](#downstream-svc)
  - [Create config-map resource](#configmap)
  - [Deployment of the application](#deploy-app)
  - [Access the reverse proxy](#access-svc)



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

The reverse proxy is implemented by the python module *reverse_proxy.py*,
which contains the routing logic and uses the app package containg
the *config* and *util* modules, as illustrated here:

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


The *config* module processes the reverse proxy configuration file,
as described next.



<a name="config" id="config"></a>
## Configuration

The proxy configuration file processed by the *config* module is determined as follows:

- if the configuration file */etc/rpx/reverse_proxy.yaml* is present, then it is used;

- otherwise, the default configuration file *config/reverse_proxy.yaml* is used,
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

In a real application, the default settings are not suitable
(for example, the setting *proxy.services[0].hosts[0].address* 
likely needs to be changed.)


To support deploy-time configuration of the reverse-proxy,
the Kubernetes *configMap* resource is used, whose content is
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
  that contains the reverse configuration to be injected
  into the reverse-proxy pod;

- *reverse-proxy-application.yaml* defines the Kubernetes
  deployment and service resources that provide the
  the reverse-proxy application, having a persistent IP address.

The config-map resource definition includes the IP address
and port of the instance(s) of the downstream services, and
it is used to inject in the reverse proxy the system configuration
*/etc/rpx/reverse_proxy.yaml*.


The next section demonstrates a full deployment example.



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

Now we create the config-map resource, which we will inject into the
reverse-proxy pod under */etc/rpx/reverse_proxy.yaml* in order to override 
the default configuration provided under *config/reverse_proxy.yaml*.

We use the information obtained at the previous step to define
the config-map resource using specification provided by the
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


The config-map resource is created using the *reverse-proxy-configmap.yaml* file:

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

Now we are ready to deploy the application: we create a deployment,
containing two pods and expose the application as a service with a
persistent IP address, using the specification contained in the
*reverse-proxy-application.yaml* file:

```yaml
$ cat reverse-proxy-application.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reverse-proxy
  namespace: default
  labels:
    app: reverse-proxy
spec:
  replicas: 2
  #revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: reverse-proxy
  template:
    metadata:
      labels:
        app: reverse-proxy
    spec:
      containers:
      - name: rpx
        image: gmateescu13/reverse-proxy:v1.0
        command: [ "/opt/rpx/reverse_proxy.py" ]
        ports:
        - containerPort: 8080
          name: http-server
          protocol: TCP
        resources:
          limits:
            memory: 500Mi
          requests:
            cpu: 500m
            memory: 400Mi
        volumeMounts:
        - mountPath: /etc/rpx
          # matches spec.volumes.configMap.name
          name: config-rproxy
          readOnly: true
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
      volumes:
      - name: config-rproxy
        configMap:
          # Matches metadata.name of configMap resource
          name: reverse-proxy-configmap
---
apiVersion: v1
kind: Service
metadata:
  namespace: default
  name: reverse-proxy
  labels:
    app: reverse-proxy
spec:
  type: NodePort
  externalTrafficPolicy: Cluster
  selector:
    app: reverse-proxy  
  ports:
  - nodePort: 30080
    port: 8080
    targetPort: 8080
    protocol: TCP
```

This file specifies two resources:
- the deployment of the application, with two pods;
- the service that exposes the application using a persistent IP address.


We deploy the application and create a service by applying the specification
defined by the *reverse-proxy-application.yaml* file:

```bash
  $ kubectl apply -f  reverse-proxy-application.yaml
  deployment.apps/reverse-proxy created
  service/reverse-proxy created

  $ kubectl describe svc reverse-proxy | egrep "^IP:|Port:|Endpoint"
  IP:                       10.100.174.188
  Port:                     <unset>  8080/TCP
  TargetPort:               8080/TCP
  NodePort:                 <unset>  30080/TCP
  Endpoints:                10.244.2.13:8080,10.244.2.14:8080
```



<a name="access-svc" id="access-svc"></a>
### Access the reverse proxy


We can access the service using curl and specifying the Host in the HTTP header:

```bash
  $ curl -isS -H "Host: my-service.my-company.com" 10.100.174.188:8080 
  HTTP/1.1 200 OK
  Content-Type: text/html
  Content-Length: 612
  Server: nginx/1.19.6
  Date: Wed, 27 Jan 2021 05:58:00 GMT
  Last-Modified: Tue, 15 Dec 2020 13:59:38 GMT
  ...
```

To test support for JSON payload, a Node.js or Flask downstream service
can be used instead of NGINX.

