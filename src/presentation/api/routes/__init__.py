from .auth_routes import router as auth_router
from .customer_routes import router as customer_router
from .event_routes import router as event_router
from .health_routes import router as health_router
from .metrics_routes import router as metrics_router
from .service_order_routes import router as service_order_router
from .vehicle_routes import router as vehicle_router

__all__ = [
    "auth_router",
    "customer_router",
    "event_router",
    "health_router",
    "metrics_router",
    "service_order_router",
    "vehicle_router",
]
