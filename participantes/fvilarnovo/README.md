# Open-Meteo by HTTP

## Overview
Monitors current weather conditions for a location using the free Open-Meteo API.

## Requirements
Zabbix version: 7.0 and higher.

## Setup
1. Link the template to a host.
2. Set {$OPENMETEO.LATITUDE} and {$OPENMETEO.LONGITUDE} on the host.

### Macros used
|Name|Description|Default|
|----|-----------|-------|
|{$OPENMETEO.LATITUDE}|Latitude of the monitored location.|`20.97`|
|{$OPENMETEO.LONGITUDE}|Longitude of the monitored location.|`-89.62`|
|{$OPENMETEO.TEMP.APPARENT.MAX.WARN}|Warning threshold of the apparent temperature, in °C.|`40`|
|{$OPENMETEO.WIND.SPEED.MAX.WARN}|Warning threshold of the wind speed, in km/h.|`50`|

### Triggers
|Name|Severity|
|----|--------|
|Weather: High apparent temperature|Warning|
|Weather: Strong wind|Average|
