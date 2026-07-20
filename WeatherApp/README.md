# 🌦️ WeatherApp

A professional, modular desktop weather application built with Python and CustomTkinter — designed with clean architecture, layered separation of concerns, and production-grade error handling rather than as a single-file script.

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-61%20passing-brightgreen.svg)

---

## 📸 Screenshots

> _Add screenshots of the running app here, e.g.:_
> `assets/screenshots/main-view-dark.png`
> `assets/screenshots/main-view-light.png`
> `assets/screenshots/forecast-cards.png`

---

## ✨ Features

### Core Weather Data
- 🔍 Search weather by city name (with input validation)
- 🌡️ Temperature, feels-like, min/max
- 💧 Humidity, pressure, wind speed, visibility, cloud coverage
- 🌅 Sunrise & sunset times (localized to the city's own timezone)
- 📍 Country, coordinates, and current local date/time
- 🖼️ Live weather condition icons (cached locally after first fetch)

### Forecast
- 📅 5-day forecast, aggregated from 3-hour resolution data
- 🌧️ Daily chance of rain
- 📊 Daily min/max temperatures

### Personalization
- 🕘 Search history (last 15 cities, most recent first)
- ⭐ Favorite cities (up to 20, toggle with one click)
- 🌓 Dark/Light theme switching
- 🌡️ Celsius / Fahrenheit unit switching
- 📍 Auto-detect location via IP geolocation

### Reliability & Resilience
- ⚠️ Graceful handling of invalid cities, no internet, timeouts, and rate limits — **the app never crashes**
- 📴 **Offline mode**: falls back to the last cached result per city when the network is unreachable
- 🔁 Automatic retry with backoff for transient network failures
- 🧵 All network calls run on background threads — the UI never freezes

### Extras
- 🌬️ Air Quality Index (AQI) with human-readable labels
- 📄 Export current report to **PDF**
- 💾 Export current report to **JSON**
- ⌨️ Keyboard shortcuts (see below)
- 📝 Structured logging (console + rotating log file)

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| UI | CustomTkinter |
| HTTP | requests |
| Images | Pillow |
| Config | python-dotenv |
| PDF export | fpdf2 |
| Testing | pytest, responses |
| Weather Data | [OpenWeatherMap API](https://openweathermap.org/api) |

---

## 🏗️ Project Structure

```
WeatherApp/
│
├── main.py                    # Application entry point
├── config.py                  # Validated, env-based configuration (Settings singleton)
├── constants.py                # Centralized constants (paths, endpoints, limits, enums)
│
├── api/
│   ├── weather_api.py          # HTTP client: requests -> typed domain models
│   └── exceptions.py           # Typed exception hierarchy for API failures
│
├── models/
│   └── weather.py              # Immutable dataclasses: WeatherReport, CurrentWeather, etc.
│
├── services/
│   ├── weather_service.py      # Orchestrates API + cache + offline fallback
│   ├── history_service.py      # Recently searched cities (JSON-persisted)
│   ├── favorites_service.py    # Favorite cities (JSON-persisted)
│   ├── cache_service.py        # TTL cache enabling offline mode
│   ├── export_service.py       # PDF / JSON report export
│   ├── geolocation_service.py  # IP-based "use my location"
│   └── json_store.py           # Shared JSON list persistence helper
│
├── ui/
│   ├── app.py                   # Main window: layout + event wiring
│   └── widgets.py                # Reusable components (SearchBar, ForecastCard, etc.)
│
├── utils/
│   ├── validators.py            # Pure input-validation functions
│   ├── helpers.py                # Formatting & conversion helpers
│   ├── icon_cache.py             # Local caching of weather icon images
│   └── logger.py                 # Centralized logging configuration
│
├── tests/                       # Unit tests (pytest)
│   ├── test_validators.py
│   ├── test_helpers.py
│   ├── test_weather_api.py
│   └── test_services.py
│
├── assets/icons/                # Cached weather icons
├── data/                        # history.json, favorites.json
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

**Why this structure?** Each layer only knows about the layer directly beneath it:
`ui` → `services` → `api` / `models` → `utils` / `config` / `constants`.
The UI never talks to `requests` directly, and the API client never touches Tkinter or the filesystem. This makes every layer independently testable (see `tests/`) and means swapping the weather provider, the persistence format, or the UI toolkit each touch only one layer.

---

## 🚀 Installation

### 1. Clone and enter the project
```bash
git clone https://github.com/yourusername/WeatherApp.git
cd WeatherApp
```

### 2. Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get a free API key
Sign up at [openweathermap.org/api](https://openweathermap.org/api) and generate a free API key.
> New keys can take a few minutes to activate.

### 5. Configure environment variables
```bash
cp .env.example .env
```
Then edit `.env` and set your real key:
```
OPENWEATHER_API_KEY=your_real_key_here
```

### 6. Run the app
```bash
python3 main.py
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + F` | Focus the search bar |
| `Ctrl + R` | Refresh current weather |
| `Ctrl + D` | Toggle dark/light mode |
| `Esc` | Clear the search bar |
| `Enter` (in search bar) | Search |

---

## 🧪 Running Tests

```bash
pip install pytest pytest-mock responses
pytest -v
```

The suite covers:
- Input validation edge cases (empty input, SQL-injection-style strings, oversized input)
- All API failure modes (404, 401, 429, timeouts, malformed JSON, missing fields)
- Retry behavior (transient vs. definitive failures)
- History/favorites/cache persistence logic, including TTL expiry and case-insensitive lookups

---

## 🩹 Error Handling Philosophy

Every user-facing failure mode maps to a specific, typed exception (see `api/exceptions.py`) rather than a bare `Exception`, so the UI can show an accurate message instead of a generic "something went wrong":

| Scenario | Behavior |
|---|---|
| Invalid/empty city name | Caught by `utils.validators` before any network call |
| City not found (404) | Clear "city not found" message, no retry |
| Invalid API key (401) | Clear configuration-error message, no retry |
| Rate limit (429) | Clear rate-limit message, no retry |
| No internet / timeout | Retried with backoff, then falls back to cached data if available |
| No internet + no cache | Clear "offline and no cached data" message |
| Malformed API response | Caught and reported instead of crashing on a `KeyError` |

---

## 🔭 Future Improvements

- [ ] Hourly forecast view (24h, using the 3-hour-resolution data already fetched)
- [ ] Interactive sunrise/sunset arc visualization
- [ ] Weather alerts (severe weather warnings) via OpenWeatherMap's One Call API
- [ ] UV Index display
- [ ] Animated weather icons/backgrounds based on condition
- [ ] Multi-language support (i18n)
- [ ] Packaged executable (PyInstaller) for one-click installs
- [ ] Optional weekly summary email export

---

## 🤝 Contributing

Contributions are welcome. Please:
1. Fork the repo and create a feature branch.
2. Follow the existing module boundaries (don't call `requests` from `ui/`, don't import Tkinter into `services/`, etc.).
3. Add or update tests for any behavior change.
4. Run `pytest` before opening a PR.
5. Keep functions typed and documented with docstrings, per the existing style.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- Weather data provided by [OpenWeatherMap](https://openweathermap.org/)
- IP geolocation via [ip-api.com](https://ip-api.com/)
- UI built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
