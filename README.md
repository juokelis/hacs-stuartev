# Stuart Energy for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Stuart Energy integration for Home Assistant allows you to monitor energy generation from your dedicated part of a solar park.

## Features

- **Energy Generation**: Track how much energy was generated from your solar park part.
- **Granular Data**: Provides hourly (or 15-minute period) data.
- **CO₂ Reduction**: Monitor the estimated CO₂ emissions avoided.
- **Historical Data**: Automatically imports historical data during setup or via options.
- **Energy Dashboard**: Compatible with the Home Assistant Energy Dashboard.

## Installation

### HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Add `https://github.com/juokelis/hacs-stuartev` as an **Integration**.
4. Search for **Stuart Energy** and click **Download**.
5. Restart Home Assistant.

### Manual

1. Download the latest release.
2. Copy the `custom_components/stuartev` folder into your `config/custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration** and search for **Stuart Energy**.
3. Enter your Stuart Energy account details:
   - **Email**: Your account email address.
   - **Password**: Your account password.
   - **Site ID**: The ID of your solar park site.
   - **Scan interval**: How often to fetch new data (in hours).
   - **Import historical data**: Number of days of historical data to import.

## Data Granularity

The integration fetches data directly from the Stuart Energy API. While it presents hourly totals in the Energy Dashboard, it processes 15-minute segments if available to ensure high accuracy.

## Energy Dashboard

To add your solar park to the Energy Dashboard:
1. Go to **Settings** -> **Dashboards** -> **Energy**.
2. Under **Solar production**, click **Add solar production**.
3. Select your `Stuart Site Energy Generated` sensor.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
