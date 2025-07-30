import requests
from typing import Dict

def  get_current_weather(region: str = "Hong Kong Observatory") -> Dict:
        """
        Get current weather observations for a specific region in Hong Kong

        Args:
            region: The region to get weather for (default: "Hong Kong Observatory")

        Returns:
            Dict containing:
            - warning: Current weather warnings
            - temperature: Current temperature in Celsius
            - humidity: Current humidity percentage
            - rainfall: Current rainfall in mm
        """
        response = requests.get(
            "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread"
        )
        data = response.json()

        # Handle warnings
        warning = "No warning in force"
        if "warningMessage" in data and data["warningMessage"]:
            warning = data["warningMessage"][0]

        # Get default values from HKO data
        default_temp = next(
            (
                t
                for t in data.get("temperature", {}).get("data", [])
                if t.get("place") == "Hong Kong Observatory"
            ),
            {"value": 25, "unit": "C", "recordTime": ""},
        )
        default_humidity = next(
            (
                h
                for h in data.get("humidity", {}).get("data", [])
                if h.get("place") == "Hong Kong Observatory"
            ),
            {"value": 60, "unit": "percent", "recordTime": ""},
        )
        # Find matching region temperature
        temp_data = data.get("temperature", {}).get("data", [])
        matched_temp = next(
            (t for t in temp_data if t["place"].lower() == region.lower()),
            {
                "place": "Hong Kong Observatory",
                "value": default_temp["value"],
                "unit": default_temp["unit"],
            },
        )
        matched_temp["recordTime"] = data["temperature"]["recordTime"]

        # Get humidity
        humidity = next(
            (
                h
                for h in data.get("humidity", {}).get("data", [])
                if h.get("place") == matched_temp["place"]
            ),
            default_humidity,
        )
        humidity["recordTime"] = data["humidity"]["recordTime"]

        # Get rainfall (0 if no rain)
        rainfall = 0
        if "rainfall" in data:
            rainfall = max(float(r.get("max", 0)) for r in data["rainfall"]["data"])
            rainfall_start = data["rainfall"]["startTime"]
            rainfall_end = data["rainfall"]["endTime"]

        return {
            "warning": warning,
            "temperature": {
                "value": matched_temp["value"],
                "unit": matched_temp["unit"],
                "recordTime": matched_temp["recordTime"],
            },
            "humidity": {
                "value": humidity["value"],
                "unit": humidity["unit"],
                "recordTime": humidity["recordTime"],
            },
            "rainfall": {"value": rainfall, "startTime": rainfall_start, "endTime": rainfall_end},
        }
