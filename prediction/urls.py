from django.urls import path
from .views import (
    predict_electricity,
    prediction_history,
    add_meter_reading,
    meter_reading_history,
    meter_reading_monthly_summary,
)

urlpatterns = [
    path("predict/", predict_electricity, name="predict_electricity"),
    path("history/", prediction_history, name="prediction_history"),
    path("meter-reading/", add_meter_reading, name="add_meter_reading"),
    path("meter-reading/history/", meter_reading_history, name="meter_reading_history"),
    path("meter-reading/monthly-summary/", meter_reading_monthly_summary,
         name="meter_reading_monthly_summary"),
]
