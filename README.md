# Live Economic Calendar

Public calendar page:

```text
https://aka-han.github.io/ZXSK/
```

ICS subscription URL:

```text
https://aka-han.github.io/ZXSK/calendar.ics
```

## What it does

- Updates every 6 hours with GitHub Actions
- Uses the Forex Factory weekly JSON feed
- Filters for USD high-impact events by default
- Adds ICS fields:
  - DESCRIPTION: Forecast / Previous / Actual / Impact / explanation
  - LOCATION: Forex Factory
  - URL: https://www.forexfactory.com/calendar
- Adds alerts:
  - 30 minutes before
  - 5 minutes before

## GitHub Pages setup

Settings → Pages → Deploy from a branch → main → /root
