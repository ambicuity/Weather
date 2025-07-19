# Dynamic GitHub Profile README Setup

This repository automatically generates and updates a dynamic GitHub profile README.md with various features including weather data, quotes, visitor counter, age calculation, and more.

## Features

✨ **Dynamic Content**:
- 🎨 Custom header with gradient background and personal info
- 😄 Daily programming jokes or inspirational quotes
- 👀 Visitor counter (file-based)
- 🎂 Dynamic age calculation
- ⌨️ Typing animation SVG
- 🧩 LeetCode progress tracking (simulated)
- 🌤️ Current weather for multiple cities

## Setup Instructions

### 1. Prerequisites

- GitHub repository for your profile (username/username)
- Python 3.11+ installed locally (for testing)

### 2. Required GitHub Secrets

Configure these secrets in your repository settings (Settings → Secrets and variables → Actions):

#### Required Secrets:
- `WEATHER_API_KEY`: Your WeatherAPI key from [weatherapi.com](https://www.weatherapi.com/)
  - Sign up for free at weatherapi.com
  - Get your API key from the dashboard
  - Add it as a repository secret

#### Optional Secrets (with defaults):
- `BIRTH_DATE`: Your birth date in YYYY-MM-DD format (default: 1995-01-01)
- `PROFILE_NAME`: Your name (default: "Developer")
- `PROFILE_TITLE`: Your title/role (default: "Full Stack Developer")
- `PROFILE_STATUS`: Current status message (default: "Building Amazing Things")
- `TYPING_TEXT`: Text for typing animation (default: "Hello, I am a Developer! 👨‍💻")

### 3. Repository Structure

```
📁 Repository Root
├── 📄 README.md                    # Auto-generated profile README
├── 📄 requirements.txt             # Python dependencies
├── 📄 SETUP.md                     # This setup guide
├── 📁 .github/workflows/
│   └── 📄 dynamic-profile-update.yml
├── 📁 scripts/
│   ├── 📄 update_profile.py        # Main orchestrator script
│   ├── 📄 weather.py               # Weather data fetcher
│   ├── 📄 quotes.py                # Daily quotes/jokes
│   ├── 📄 visitor_counter.py       # Visitor counter
│   ├── 📄 age_calculator.py        # Dynamic age calculation
│   ├── 📄 typing_animation.py      # Typing animation SVG
│   ├── 📄 header_generator.py      # Custom header SVG
│   └── 📄 leetcode_progress.py     # LeetCode progress tracker
└── 📁 assets/
    ├── 📄 header.svg               # Generated header image
    └── 📄 typing_animation.svg     # Generated typing animation
```

### 4. Workflow Schedule

The GitHub Action runs:
- **Automatically**: Every 6 hours (4 times daily)
- **Manually**: Via workflow dispatch in GitHub Actions tab

### 5. Local Testing

To test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export WEATHER_API_KEY="your_api_key_here"
export BIRTH_DATE="1990-01-01"
export PROFILE_NAME="Your Name"

# Run the update script
python scripts/update_profile.py
```

### 6. Customization

#### Weather Cities
Edit `scripts/weather.py` to change the cities displayed:
```python
cities = ['YourCity', 'AnotherCity', 'ThirdCity']
```

#### LeetCode Progress
Edit `scripts/leetcode_progress.py` to update your actual progress:
```python
'total_solved': 250,  # Your actual count
'easy_solved': 120,
'medium_solved': 100,
'hard_solved': 30,
```

#### Quote Sources
Edit `scripts/quotes.py` to change quote APIs or add custom quotes.

#### Styling
- Header colors: Edit `scripts/header_generator.py`
- README layout: Edit `scripts/update_profile.py`

### 7. API Information

**Weather API**: [WeatherAPI.com](https://www.weatherapi.com/)
- Free tier: 1 million calls/month
- No credit card required for signup
- Provides current weather, forecasts, and historical data

**Quotes API**: 
- Programming jokes: [JokeAPI](https://jokeapi.dev/)
- Inspirational quotes: [Quotable](https://quotable.io/)
- Both are free with no API key required

### 8. Troubleshooting

#### Common Issues:

1. **Weather data showing "unavailable"**
   - Check if WEATHER_API_KEY secret is set correctly
   - Verify API key is valid at weatherapi.com
   - Fallback data will be used if API fails

2. **Age not updating**
   - Check BIRTH_DATE secret format (YYYY-MM-DD)
   - Ensure workflow has proper permissions

3. **Workflow not running**
   - Check if GitHub Actions are enabled for your repository
   - Verify workflow file syntax with GitHub Actions validator

4. **Images not displaying**
   - Ensure assets/ directory is committed to repository
   - Check SVG file generation in workflow logs

### 9. Contributing

Feel free to:
- Add new dynamic content features
- Improve existing scripts
- Enhance the README template
- Add more customization options

### 10. License

This project is open source. Feel free to use and modify for your own profile!

---

**🚀 Happy coding!** Your dynamic profile README will automatically stay fresh and engaging.