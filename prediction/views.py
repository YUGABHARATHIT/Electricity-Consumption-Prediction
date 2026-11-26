
import joblib
import pandas as pd

from pathlib import Path
from django.conf import settings
from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import PredictionHistory


# Load trained ML model
MODEL_PATH = Path(settings.BASE_DIR) / "electricity_prediction_model.joblib"

saved_data = joblib.load(MODEL_PATH)

model = saved_data["model"]
feature_columns = saved_data["feature_columns"]


# Home page
def home(request):
    return render(request, "prediction/index.html")


# Electricity prediction API
@api_view(["POST"])
def predict_electricity(request):
    try:
        input_data = pd.DataFrame([request.data])

        input_data = input_data[feature_columns]

        prediction = model.predict(input_data)[0]

        # Save prediction in database
        PredictionHistory.objects.create(
            power=float(input_data["power"].iloc[0]),
            predicted_consumption=float(prediction)
        )

        return Response({
            "predicted_consumption": round(float(prediction), 3),
            "unit": "kW"
        })

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


# Prediction history API
@api_view(["GET"])
def prediction_history(request):
    history = PredictionHistory.objects.all().order_by("-created_at")

    data = []

    for item in history:
        data.append({
            "power": item.power,
            "predicted_consumption": item.predicted_consumption,
            "created_at": item.created_at
        })

    return Response(data)

