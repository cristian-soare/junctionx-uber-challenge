import pandas as pd


def train_weather_model(weather_df):
  """Compute transition probabilities P(next | current) per city."""
  transitions = {}
  for city, group in weather_df.groupby("city_id"):
    group = group.sort_values("date")
    group["next_weather"] = group["weather"].shift(-1)
    trans = (
      group.groupby(["weather", "next_weather"])
      .size()
      .unstack(fill_value=0)
      .apply(lambda x: x / x.sum(), axis=1)
    )
    transitions[city] = trans
  return transitions


def predict_weather(city_id, target_date, weather_df, transitions):
  """Predict next weather for city_id on target_date using transition probs."""
  weather_df["date"] = pd.to_datetime(weather_df["date"])
  target_date = pd.to_datetime(target_date)

  # Get last known weather before target date
  recent = weather_df[(weather_df["city_id"] == city_id) & (weather_df["date"] < target_date)]
  if recent.empty:
    # fallback to most frequent
    most_common = weather_df[weather_df["city_id"] == city_id]["weather"].mode()[0]
    return most_common

  last_weather = recent.sort_values("date").iloc[-1]["weather"]

  # Transition-based prediction
  if city_id in transitions and last_weather in transitions[city_id].index:
    probs = transitions[city_id].loc[last_weather]
    if not probs.empty:
      return probs.idxmax()  # most probable next weather

  # Fallback: most frequent weather
  return recent["weather"].mode()[0]


def get_weather_multiplier(weather_condition):
  """Convert weather condition to earning multiplier."""
  weather_multipliers = {
    "Clear": 1.0,
    "Rain": 1.2,
    "Snow": 1.3,
  }
  return weather_multipliers.get(weather_condition, 1.0)


def load_weather_data(csv_path="/app/data/weather_daily.csv"):
  """Load weather data and train transition model."""
  weather_df = pd.read_csv(csv_path)
  transitions = train_weather_model(weather_df)
  return weather_df, transitions


def get_weather_for_date(city_id, date):
  """Get weather prediction and multiplier for a city on a specific date.

  Args:
      city_id: City ID
      date: Date string (YYYY-MM-DD)

  Returns:
      Tuple of (weather_condition, weather_multiplier)

  """
  weather_df, transitions = load_weather_data()
  pred = predict_weather(city_id, date, weather_df, transitions)
  multiplier = get_weather_multiplier(pred)
  return pred, multiplier
