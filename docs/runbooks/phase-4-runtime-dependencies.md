# Phase 4 Runtime Dependencies

This runbook starts the shared low-cost dependencies for the Phase 4 demo in k3s.

## Apply RabbitMQ and MongoDB

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/runtime-dependencies/rabbitmq.yaml
kubectl apply -f k8s/runtime-dependencies/mongodb.yaml
```

## Demo URLs

- RabbitMQ AMQP: `rabbitmq.service-order.svc.cluster.local:5672`
- RabbitMQ management: `rabbitmq.service-order.svc.cluster.local:15672`
- MongoDB: `mongodb.service-order.svc.cluster.local:27017`

## Secret Handling

The checked-in manifests use `change-me` placeholders only. Rotate the credentials in the cluster before a real demo:

```bash
kubectl create secret generic rabbitmq-secret \
  -n service-order \
  --from-literal=RABBITMQ_DEFAULT_USER=service-order \
  --from-literal=RABBITMQ_DEFAULT_PASS='<strong-password>' \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic mongodb-secret \
  -n service-order \
  --from-literal=MONGO_INITDB_ROOT_USERNAME=service-order \
  --from-literal=MONGO_INITDB_ROOT_PASSWORD='<strong-password>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Service Environment Examples

```bash
RABBITMQ_URL=amqp://service-order:<password>@rabbitmq.service-order.svc.cluster.local:5672/%2F
MONGODB_URL=mongodb://service-order:<password>@mongodb.service-order.svc.cluster.local:27017/service_order?authSource=admin
```

Keep one replica for RabbitMQ and MongoDB during the academic demo to reduce AWS Academy cost.
