# rpx

## System architecture

![alt text][arch]

[arch]: images/arch.png "System architecture"


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
