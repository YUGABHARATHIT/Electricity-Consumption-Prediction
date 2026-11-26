
from django.db import models


class PredictionHistory(models.Model):
    power = models.FloatField()
    predicted_consumption = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.predicted_consumption} kW"


class DailyMeterReading(models.Model):
    reading_date = models.DateField(unique=True)
    meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reading_date} - {self.meter_reading} kWh"

