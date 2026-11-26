import joblib
import pandas as pd

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.utils.dateparse import parse_date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import PredictionHistory, DailyMeterReading


# Load the trained hourly prediction model.
MODEL_PATH = Path(settings.BASE_DIR) / "electricity_prediction_model.joblib"
saved_data = joblib.load(MODEL_PATH)
model = saved_data["model"]
feature_columns = saved_data["feature_columns"]


def home(request):
    return render(request, "prediction/index.html")


@api_view(["POST"])
def predict_electricity(request):
    try:
        input_data = pd.DataFrame([request.data])
        input_data = input_data[feature_columns]
        prediction = model.predict(input_data)[0]

        PredictionHistory.objects.create(
            power=float(input_data["power"].iloc[0]),
            predicted_consumption=float(prediction)
        )

        return Response({
            "predicted_consumption": round(float(prediction), 3),
            "unit": "kW"
        })
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def prediction_history(request):
    history = PredictionHistory.objects.all().order_by("-created_at")
    data = [{
        "power": item.power,
        "predicted_consumption": item.predicted_consumption,
        "created_at": item.created_at
    } for item in history]
    return Response(data)


@api_view(["POST"])
def add_meter_reading(request):
    reading_date = request.data.get("reading_date")
    meter_reading = request.data.get("meter_reading")

    if not reading_date or meter_reading is None:
        return Response(
            {"error": "Date and meter reading are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    date_value = parse_date(str(reading_date))
    if date_value is None:
        return Response(
            {"error": "Invalid date. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        current_reading = Decimal(str(meter_reading))
    except (InvalidOperation, ValueError, TypeError):
        return Response(
            {"error": "Enter a valid meter reading."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not current_reading.is_finite() or current_reading < 0:
        return Response(
            {"error": "Meter reading must be a non-negative number."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if DailyMeterReading.objects.filter(reading_date=date_value).exists():
        return Response(
            {"error": "A reading already exists for this date."},
            status=status.HTTP_400_BAD_REQUEST
        )

    previous = DailyMeterReading.objects.filter(
        reading_date__lt=date_value
    ).order_by("-reading_date").first()

    following = DailyMeterReading.objects.filter(
        reading_date__gt=date_value
    ).order_by("reading_date").first()

    if previous and current_reading < previous.meter_reading:
        return Response(
            {"error": "Reading cannot be lower than the previous saved reading."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if following and current_reading > following.meter_reading:
        return Response(
            {"error": "Reading cannot be higher than the next saved reading."},
            status=status.HTTP_400_BAD_REQUEST
        )

    reading = DailyMeterReading.objects.create(
        reading_date=date_value,
        meter_reading=current_reading
    )

    consumption = None
    interval_days = None
    average_daily = None

    if previous:
        interval_days = (date_value - previous.reading_date).days
        consumption = float(current_reading - previous.meter_reading)
        average_daily = round(consumption / interval_days, 3)

    return Response({
        "message": "Meter reading saved successfully.",
        "reading_date": str(reading.reading_date),
        "meter_reading": str(reading.meter_reading),
        "consumption_kwh": consumption,
        "interval_days": interval_days,
        "average_daily_consumption_kwh": average_daily
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def meter_reading_history(request):
    readings = DailyMeterReading.objects.order_by("reading_date")
    history = []
    previous = None

    for reading in readings:
        consumption = None
        interval_days = None
        average_daily = None

        if previous:
            interval_days = (reading.reading_date - previous.reading_date).days
            consumption = float(reading.meter_reading - previous.meter_reading)
            average_daily = round(consumption / interval_days, 3) if interval_days else None

        history.append({
            "reading_date": str(reading.reading_date),
            "meter_reading": str(reading.meter_reading),
            "consumption_kwh": consumption,
            "interval_days": interval_days,
            "average_daily_consumption_kwh": average_daily
        })
        previous = reading

    return Response({
        "total_readings": len(history),
        "history": history
    })


@api_view(["GET"])
def meter_reading_monthly_summary(request):
    readings = list(DailyMeterReading.objects.order_by("reading_date"))
    monthly_totals = defaultdict(float)
    previous = None

    for reading in readings:
        if previous:
            month_key = reading.reading_date.strftime("%Y-%m")
            monthly_totals[month_key] += float(
                reading.meter_reading - previous.meter_reading
            )
        previous = reading

    summary = [
        {"month": month, "consumption_kwh": round(total, 3)}
        for month, total in sorted(monthly_totals.items())
    ]

    return Response({
        "months_available": len(summary),
        "monthly_summary": summary,
        "note": (
            "Each interval's consumption is assigned to the month of its later reading. "
            "If readings are missing, the interval may cover multiple days or cross months."
        )
    })
