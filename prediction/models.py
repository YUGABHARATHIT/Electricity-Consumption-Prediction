from django.db import models

# Create your models here.
from django.db import models

class PredictionHistory(models.Model):

    power = models.FloatField()
    predicted_consumption = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.predicted_consumption} kW"
