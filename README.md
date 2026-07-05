# service-order-os-service

FastAPI microservice responsible for the service order lifecycle in the FIAP Phase 4 service-order system.

## Responsibility

This service owns the service order identity, status history, Saga orchestration state, and lifecycle events. It does not read Billing or Execution databases.

## Architecture

- `src/domain`: service order entity, status transitions, history, and domain events.
- `src/application`: use cases and ports for repositories and event publishers.
- `src/infrastructure`: settings, logging, repositories, observability, and messaging adapters.
- `src/presentation`: FastAPI routes, request/response schemas, and HTTP dependencies.

Business rules stay in `domain` and `application`; HTTP, queue, and persistence details stay at the edges.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/service-orders` | Open a service order and publish `OS_OPENED`. |
| `GET` | `/service-orders/{service_order_id}` | Read a service order and its status history. |
| `POST` | `/service-orders/{service_order_id}/events` | Apply a Saga event to the service order state. |
| `GET` | `/events` | List published in-memory events for demo/test evidence. |
| `POST` | `/events/drain` | Drain published in-memory events for demo/test evidence. |
| `GET` | `/health` | Health check. |
| `GET` | `/health/live` | Liveness check. |
| `GET` | `/health/ready` | Readiness check. |
| `GET` | `/metrics` | Prometheus-style metrics endpoint. |

Swagger is available at `/docs` when the app is running.

## Events

Published by this service:

- `OS_OPENED`
- `PAYMENT_PENDING`
- `EXECUTION_REQUESTED`
- `OS_COMPLETED`
- `OS_COMPENSATION_REQUIRED`

Consumed by the Saga handler:

- `QUOTE_APPROVED`
- `PAYMENT_PREFERENCE_CREATED`
- `PAYMENT_CONFIRMED`
- `EXECUTION_STARTED`
- `EXECUTION_COMPLETED`
- `QUOTE_FAILED`
- `PAYMENT_FAILED`
- `EXECUTION_ENQUEUE_FAILED`
- `EXECUTION_FAILED`

The event envelope is JSON with `event_id`, `event_type`, `correlation_id`, `occurred_at`, and `payload`.

## Saga Rules

The orchestrated Saga lives in this service. The happy path is:

1. Open service order.
2. Receive quote approval.
3. Receive payment preference creation.
4. Receive payment confirmation.
5. Request execution.
6. Receive execution start and completion.
7. Mark the service order as completed.

Compensation paths mark the service order with a failure or review status and publish `OS_COMPENSATION_REQUIRED`.

## Runtime Mode

`APP_RUNTIME_MODE` controls infrastructure adapters:

- `memory`: uses in-memory repository and publisher for local tests and fast demos.
- `real`: uses SQLAlchemy PostgreSQL repository and RabbitMQ publisher.

## Messaging

RabbitMQ integration is represented by thin infrastructure adapters:

- `RabbitMqEventPublisher`
- `RabbitMqEventConsumer`

Automated tests use fake channels only. They do not connect to production queues. In `real` runtime mode, the app publishes events to RabbitMQ through `RabbitMqBlockingEventPublisher`.

Environment variables:

- `RABBITMQ_URL`
- `RABBITMQ_EXCHANGE`
- `RABBITMQ_ROUTING_KEY`
- `RABBITMQ_QUEUE`

## Database

The OS boundary has a SQLAlchemy repository for service orders and status history. `APP_RUNTIME_MODE=real` uses `DATABASE_URL`; `APP_RUNTIME_MODE=memory` keeps the local in-memory repository for tests.

## Local Development

```bash
uv sync --dev
make lint
make test
make test-cov
make run-dev
```

## Validation Evidence

Latest local validation for Phase 7:

- `uv run --dev black src tests`
- `uv run --dev isort src tests`
- `uv run --dev black --check src tests`
- `uv run --dev isort --check-only src tests`
- `uv run --dev flake8 src tests`
- `uv run --dev pytest --cov=src --cov-report=term-missing --cov-report=xml -q`

Result: `29 passed`, `92%` coverage.

BDD evidence:

- `tests/bdd/test_saga_happy_path.py`

## CI/CD and Deploy

The GitHub Actions workflow validates lint, tests, coverage, SonarCloud, image build/push to GHCR, manifest rendering, and k3s deployment.

Kubernetes manifests are under `k8s/`. Manifests must be rendered with an explicit GHCR image before applying to the cluster.

## Cost Notes

The target demo uses EC2 with k3s, GHCR images, RabbitMQ inside k3s, and shared low-cost infrastructure to stay within the AWS Academy budget.
