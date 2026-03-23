# MyFuelPortal — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Monitor your propane (or other fuel) tank levels, deliveries, and daily usage in Home Assistant via [MyFuelPortal](https://www.myfuelportal.com/). Many fuel providers use MyFuelPortal for online tank monitoring — this integration scrapes your provider's portal and creates sensors for each tank.

## Features

- **Works with any MyFuelPortal provider** — enter your provider's subdomain during setup
- **Per-tank device grouping** — each tank appears as its own device in HA
- **Energy dashboard ready** — Cumulative Usage sensor with `state_class: total_increasing`
- **Auto-refresh** every 12 hours (matches portal update frequency)
- **State restoration** — cumulative usage survives HA restarts

## Sensors

| Sensor | Description | State Class |
|--------|-------------|-------------|
| Gallons | Current gallons in tank | `measurement` |
| Level | Tank fill percentage (%) | `measurement` |
| Capacity | Tank capacity (gallons) | — |
| Last Delivery | Date of last fuel delivery | — |
| Reading Date | Date of last monitor reading | — |
| Daily Usage | Estimated gallons/day | `measurement` |
| Cumulative Usage | Total gallons consumed (for Energy dashboard) | `total_increasing` |

## Installation

### HACS (Recommended)

1. Open **HACS** → **Integrations** → click the **⋮** menu (top right) → **Custom repositories**
2. Enter this repository URL and select **Integration** as the category:
   ```
   https://github.com/DeltaNu1142/MyFuelPortal
   ```
3. Click **Add**, then find **MyFuelPortal** in the HACS store and click **Install**
4. **Restart Home Assistant**

### Manual

1. Download this repository
2. Copy the `custom_components/myfuelportal/` folder into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **MyFuelPortal**
3. Enter:
   - **Provider subdomain** — the part before `.myfuelportal.com` in your provider's portal URL (e.g., if your portal is at `https://myprovider.myfuelportal.com`, enter `myprovider`)
   - **Email address** — your MyFuelPortal login email
   - **Password** — your MyFuelPortal password
4. Sensors for your tank(s) will appear automatically, grouped under a device per tank

## Energy Dashboard

To track propane consumption in the Energy dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Under **Gas consumption**, click **Add gas source**
3. Select the **Cumulative Usage** sensor for your tank
4. Optionally configure a fixed cost per unit (your price per gallon)

The Cumulative Usage sensor tracks total gallons consumed over time. It increases as your tank level drops between deliveries and correctly handles refills (tank level going up).

## How It Works

The integration logs into your provider's MyFuelPortal site, navigates to the tank page, and scrapes the current tank data. Your provider's satellite tank monitor typically updates readings at least once per day.

- Data refreshes every **12 hours**
- Login uses the standard MyFuelPortal web interface
- Supports accounts with **multiple tanks**

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Invalid credentials | Double-check your MyFuelPortal email and password |
| Cannot connect | Verify your HA instance can reach `https://<provider>.myfuelportal.com` |
| No sensors created | Ensure your MyFuelPortal account has active tank data |
| Energy dashboard not updating | Wait for the next 12-hour refresh cycle, or restart the integration |

## Requirements

- Home Assistant **2023.7** or later
- A MyFuelPortal account with your fuel provider

## Credits

Original integration by [DeltaNu1142](https://github.com/DeltaNu1142). Refactored for HACS compatibility, configurable providers, bug fixes, and Home Assistant best practices.

### Changes from Original

- **Configurable provider** — config flow prompts for subdomain; no code editing required
- **HACS-compatible** — proper `custom_components/` structure, `hacs.json`, translations
- **Bug fixes** — `CumulativeUsageSensor` referenced undefined `self._tank_name`; `gallons` sensor had incorrect `state_class` (`TOTAL_INCREASING` → `MEASUREMENT`); duplicate coordinator removed
- **Best practices** — `CoordinatorEntity` base class, `SensorEntity`, device grouping per tank, proper units (`UnitOfVolume.GALLONS`), icons, state restoration for cumulative sensor
