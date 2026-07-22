# Phase 4 Runtime Dependencies

This runbook starts the shared low-cost dependencies for the Phase 4 demo in k3s.

## Apply RabbitMQ

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/runtime-dependencies/rabbitmq.yaml
```

## Demo URLs

- RabbitMQ AMQP: `rabbitmq.service-order.svc.cluster.local:5672`
- RabbitMQ management: `rabbitmq.service-order.svc.cluster.local:15672`

## Secret Handling

The checked-in manifests use `change-me` placeholders only. Rotate the credentials in the cluster before a real demo:

```bash
kubectl create secret generic rabbitmq-secret \
  -n service-order \
  --from-literal=RABBITMQ_DEFAULT_USER=service-order \
  --from-literal=RABBITMQ_DEFAULT_PASS='<strong-password>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Service Environment Examples

```bash
RABBITMQ_URL=amqp://service-order:<password>@rabbitmq.service-order.svc.cluster.local:5672/%2F
```

Keep one replica for RabbitMQ during the academic demo to reduce AWS Academy cost.
