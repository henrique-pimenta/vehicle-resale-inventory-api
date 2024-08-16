from django.urls import path, include
from rest_framework.routers import DefaultRouter

from inventory.apps.vehicle.views import VehicleViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
