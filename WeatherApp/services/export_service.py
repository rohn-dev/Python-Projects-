"""
services/export_service.py
----------------------------
Exports a WeatherReport to JSON or PDF for the user to save/share.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from constants import EXPORTS_DIR
from models.weather import WeatherReport
from utils.helpers import format_temperature
from utils.logger import get_logger

logger = get_logger(__name__)


class ExportService:
    """Handles exporting weather reports to disk in various formats."""

    def __init__(self, export_dir: Path | None = None) -> None:
        self._export_dir = export_dir or EXPORTS_DIR
        self._export_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, report: WeatherReport) -> Path:
        """
        Export `report` as a pretty-printed JSON file.

        Returns:
            The path to the written file.
        """
        filename = self._build_filename(report, "json")
        path = self._export_dir / filename

        payload = asdict(report)
        payload["current"]["sunrise"] = report.current.sunrise.isoformat()
        payload["current"]["sunset"] = report.current.sunset.isoformat()
        payload["current"]["observed_at"] = report.current.observed_at.isoformat()
        for day in payload["daily_forecast"]:
            day["date"] = report.current.observed_at.isoformat() if False else str(day["date"])
            for entry in day["entries"]:
                entry["timestamp"] = str(entry["timestamp"])

        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

        logger.info("Exported weather report to JSON: %s", path)
        return path

    def export_pdf(self, report: WeatherReport) -> Path:
        """
        Export `report` as a simple, readable PDF report using fpdf2.

        Returns:
            The path to the written file.
        """
        from fpdf import FPDF

        filename = self._build_filename(report, "pdf")
        path = self._export_dir / filename
        units = report.current.units

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 12, f"Weather Report: {report.current.city}, {report.current.country}", ln=True)

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Current Conditions", ln=True)
        pdf.set_font("Helvetica", "", 11)

        lines = [
            f"Temperature: {format_temperature(report.current.temperature, units)}",
            f"Feels Like: {format_temperature(report.current.feels_like, units)}",
            f"Condition: {report.current.condition.description}",
            f"Humidity: {report.current.humidity}%",
            f"Pressure: {report.current.pressure} hPa",
            f"Wind Speed: {report.current.wind_speed}",
            f"Visibility: {report.current.visibility_km} km",
            f"Cloud Coverage: {report.current.cloud_coverage}%",
            f"Sunrise: {report.current.sunrise.strftime('%I:%M %p')}",
            f"Sunset: {report.current.sunset.strftime('%I:%M %p')}",
            f"Coordinates: {report.current.coordinates.latitude}, {report.current.coordinates.longitude}",
        ]
        for line in lines:
            pdf.cell(0, 8, line, ln=True)

        if report.air_quality:
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Air Quality", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, f"AQI: {report.air_quality.aqi} ({report.air_quality.label})", ln=True)
            pdf.cell(0, 8, f"PM2.5: {report.air_quality.pm2_5} | PM10: {report.air_quality.pm10}", ln=True)

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "5-Day Forecast", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for day in report.daily_forecast:
            pdf.cell(
                0, 8,
                f"{day.date.strftime('%a, %d %b')}: "
                f"{format_temperature(day.temp_max, units)} / {format_temperature(day.temp_min, units)}"
                f" - {day.condition.description} (Rain: {round(day.max_chance_of_rain * 100)}%)",
                ln=True,
            )

        pdf.output(str(path))
        logger.info("Exported weather report to PDF: %s", path)
        return path

    @staticmethod
    def _build_filename(report: WeatherReport, extension: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_city = report.current.city.replace(" ", "_")
        return f"{safe_city}_{timestamp}.{extension}"
