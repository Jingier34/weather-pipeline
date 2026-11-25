from datetime import date, timedelta

import pandas as pd
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_FIELDS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"]

# Five cities with very different climates
CITIES = {
    "Seattle": (47.61, -122.33),
    "New York": (40.71, -74.01),
    "Chicago": (41.88, -87.63),
    "Miami": (25.76, -80.19),
    "Denver": (39.74, -104.99),
}


def fetch_city(name, latitude, longitude, start, end):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_FIELDS),
        "timezone": "auto",
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=30)
    response.raise_for_status()
    daily = response.json()["daily"]
    frame = pd.DataFrame(daily).rename(columns={"time": "date"})
    frame.insert(0, "city", name)
    return frame


def main():
    # The archive API lags a few days behind, so stop a week before today
    end = date.today() - timedelta(days=7)
    start = end - timedelta(days=29)

    frames = [fetch_city(name, lat, lon, start, end) for name, (lat, lon) in CITIES.items()]
    data = pd.concat(frames, ignore_index=True)

    print(f"Rows: {len(data)}  ({len(CITIES)} cities x {len(data) // len(CITIES)} days)")
    print(f"Date range: {data['date'].min()} to {data['date'].max()}")
    print("\nColumns:", ", ".join(data.columns))

    print("\nMissing values per column:")
    print(data.isna().sum())

    print("\nSummary by city:")
    summary = data.groupby("city").agg(
        avg_high=("temperature_2m_max", "mean"),
        avg_low=("temperature_2m_min", "mean"),
        total_precip_mm=("precipitation_sum", "sum"),
        rainy_days=("precipitation_sum", lambda s: (s > 0).sum()),
    ).round(1)
    print(summary)

    print("\nFirst rows:")
    print(data.head())


if __name__ == "__main__":
    main()