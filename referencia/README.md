# Open-Meteo by HTTP

## Overview

Monitors current weather conditions for a location using the free Open-Meteo forecast API (https://open-meteo.com).
No API key is required. Set {$OPENMETEO.LATITUDE} and {$OPENMETEO.LONGITUDE} on the host to the location you want to monitor.
The defaults point to Mérida, Yucatán, Mexico.

Template created for the CCOSS 2026 contribution workshop.

## Requirements

Zabbix version: 7.0 and higher.

## Tested versions

This template has been tested on:
- Open-Meteo Forecast API v1 (https://open-meteo.com/en/docs)

## Configuration

> Zabbix should be configured according to the instructions in the [Templates out of the box](https://www.zabbix.com/documentation/7.0/manual/config/templates_out_of_the_box) section.

## Setup

1. Make sure the Zabbix server or proxy that monitors the host can reach `https://api.open-meteo.com` (set {$OPENMETEO.HTTP.PROXY} if it needs a proxy).
2. Import the template and link it to a host (the host does not need an interface).
3. Set {$OPENMETEO.LATITUDE} and {$OPENMETEO.LONGITUDE} on the host to the location to monitor. Tune the threshold macros if needed.

Open-Meteo is free for non-commercial use, up to 10,000 calls per day. With the default interval of 15m this template makes 96 calls per day per host.

### Macros used

|Name|Description|Default|
|----|-----------|-------|
|{$OPENMETEO.HTTP.PROXY}|<p>HTTP proxy for requests to the Open-Meteo API. Leave empty for direct access.</p>||
|{$OPENMETEO.LATITUDE}|<p>Latitude of the monitored location, in decimal degrees. Default: Mérida, Yucatán.</p>|`20.97`|
|{$OPENMETEO.LONGITUDE}|<p>Longitude of the monitored location, in decimal degrees. Default: Mérida, Yucatán.</p>|`-89.62`|
|{$OPENMETEO.TEMP.APPARENT.MAX.CRIT}|<p>Critical threshold of the apparent temperature, in °C.</p>|`45`|
|{$OPENMETEO.TEMP.APPARENT.MAX.WARN}|<p>Warning threshold of the apparent temperature, in °C.</p>|`40`|
|{$OPENMETEO.TIMEOUT}|<p>Timeout of requests to the Open-Meteo API.</p>|`10s`|
|{$OPENMETEO.UV.INDEX.MAX.WARN}|<p>Warning threshold of the UV index.</p>|`8`|
|{$OPENMETEO.WIND.SPEED.MAX.WARN}|<p>Warning threshold of the wind speed, in km/h.</p>|`50`|

### Items

|Name|Description|Type|Key and additional info|
|----|-----------|----|-----------------------|
|Weather: Apparent temperature|<p>Apparent ("feels like") temperature at 2 meters above ground, combining air temperature, humidity and wind.</p>|Dependent item|openmeteo.temperature.apparent<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.apparent_temperature`</p></li></ul>|
|Weather: Get current conditions|<p>Master item: raw JSON with the current conditions returned by the Open-Meteo forecast API. Open-Meteo refreshes current data every 15 minutes. Dependent items extract individual metrics.</p>|HTTP agent|openmeteo.current.get|
|Weather: Relative humidity|<p>Relative humidity at 2 meters above ground, in %.</p>|Dependent item|openmeteo.humidity<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.relative_humidity_2m`</p></li></ul>|
|Weather: Precipitation|<p>Total precipitation (rain, showers, snow) in the preceding 15 minutes, in millimeters.</p>|Dependent item|openmeteo.precipitation<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.precipitation`</p></li></ul>|
|Weather: Temperature|<p>Air temperature at 2 meters above ground.</p>|Dependent item|openmeteo.temperature<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.temperature_2m`</p></li></ul>|
|Weather: UV index|<p>UV index. 0-2 low, 3-5 moderate, 6-7 high, 8-10 very high, 11+ extreme.</p>|Dependent item|openmeteo.uv.index<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.uv_index`</p></li></ul>|
|Weather: Weather condition|<p>Current weather condition as a WMO weather interpretation code (0 - clear sky, 61 - slight rain, 95 - thunderstorm...).</p>|Dependent item|openmeteo.weather.code<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.weather_code`</p></li><li><p>Discard unchanged with heartbeat: `6h`</p></li></ul>|
|Weather: Wind speed|<p>Wind speed at 10 meters above ground, in km/h.</p>|Dependent item|openmeteo.wind.speed<p>**Preprocessing**</p><ul><li><p>JSON Path: `$.current.wind_speed_10m`</p></li></ul>|

### Triggers

|Name|Description|Expression|Severity|Dependencies and additional info|
|----|-----------|----------|--------|--------------------------------|
|Weather: Extreme heat|<p>The apparent temperature has stayed above {$OPENMETEO.TEMP.APPARENT.MAX.CRIT}°C for 30 minutes. Risk of heat stroke for people working outdoors.</p>|`min(/Open-Meteo by HTTP/openmeteo.temperature.apparent,30m)>{$OPENMETEO.TEMP.APPARENT.MAX.CRIT}`|High||
|Weather: High apparent temperature|<p>The apparent temperature has stayed above {$OPENMETEO.TEMP.APPARENT.MAX.WARN}°C for 30 minutes.</p>|`min(/Open-Meteo by HTTP/openmeteo.temperature.apparent,30m)>{$OPENMETEO.TEMP.APPARENT.MAX.WARN}`|Warning|**Depends on**:<br><ul><li>Weather: Extreme heat</li></ul>|
|Weather: Failed to fetch weather data|<p>Zabbix has not received data from the Open-Meteo API for the last hour. Check internet access from the Zabbix server or proxy, and the coordinates in {$OPENMETEO.LATITUDE} and {$OPENMETEO.LONGITUDE}.</p>|`nodata(/Open-Meteo by HTTP/openmeteo.current.get,1h)=1`|Warning||
|Weather: Very high UV index|<p>The UV index has been {$OPENMETEO.UV.INDEX.MAX.WARN} or higher for 30 minutes. Unprotected skin can burn in minutes.</p>|`min(/Open-Meteo by HTTP/openmeteo.uv.index,30m)>={$OPENMETEO.UV.INDEX.MAX.WARN}`|Warning||
|Weather: Thunderstorm|<p>Open-Meteo reports a thunderstorm (WMO code 95 or higher) at the monitored location.</p>|`last(/Open-Meteo by HTTP/openmeteo.weather.code)>=95`|Average||
|Weather: Strong wind|<p>Wind speed has stayed above {$OPENMETEO.WIND.SPEED.MAX.WARN} km/h for 30 minutes.</p>|`min(/Open-Meteo by HTTP/openmeteo.wind.speed,30m)>{$OPENMETEO.WIND.SPEED.MAX.WARN}`|Average||

## Feedback

Please report any issues with the template at [`https://support.zabbix.com`](https://support.zabbix.com)

You can also provide feedback, discuss the template, or ask for help at [`ZABBIX forums`](https://www.zabbix.com/forum/zabbix-suggestions-and-feedback)
