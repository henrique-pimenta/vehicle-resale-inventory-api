from enum import Enum

from django.db import models


class VehicleStatus(Enum):
    AVAILABLE = "available"
    SELECTED = "selected"
    SOLD = "sold"


class Vehicle(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    status = models.CharField(
        max_length=9,
        choices=[(status.value, status.value) for status in VehicleStatus],
        default=VehicleStatus.AVAILABLE.value,
    )
    renavam = models.IntegerField()
    license_plate = models.CharField(max_length=7)
    make = models.CharField(max_length=36)
    model = models.CharField(max_length=36)
    color = models.CharField(max_length=36)
    year = models.IntegerField()
    kilometerage = models.IntegerField()
    price_cents = models.IntegerField()
