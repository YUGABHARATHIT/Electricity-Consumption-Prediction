from django.urls import path
from .views import predict_electricity, prediction_history

urlpatterns = [
    path("predict/", predict_electricity, name="predict_electricity"),
    path("history/", prediction_history, name="prediction_history"),
]
