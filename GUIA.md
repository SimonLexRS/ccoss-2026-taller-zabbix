# De cero a Pull Request: tu primer template para Zabbix

Guía del taller · CCOSS 2026 · Mérida, Yucatán

> Sigue esta guía a tu ritmo. Si te atoras, al final de cada parte hay un ✅ **checkpoint**: avísalo o levanta la mano. Si te quedas atrás, puedes importar el template de referencia y saltar a la parte 3.

---

## Parte 0 · Antes de empezar (5 min)

Necesitas:

- Un navegador.
- Una cuenta de GitHub, con sesión iniciada: https://github.com/signup
- Un usuario del taller (opcional): entra a **https://taller-ccoss-2026-webapp-production.up.railway.app/**, escribe el **código que aparece en pantalla** y pulsa *Quiero mi usuario*.

Recibirás algo así:

| Dato | Ejemplo |
|---|---|
| Zabbix | `https://facu-demo.zabbix.cloud` |
| Usuario | `ccoss07` |
| Tu host de práctica | `ccoss07` |
| Tu grupo | `CCOSS 2026/ccoss07` |

Entra a Zabbix con tu usuario. Si quieres la interfaz en español: *User settings* → *Profile* → *Language*.

> Todo lo que crees debe llevar tu sufijo, por ejemplo `Open-Meteo by HTTP - ccoss07`. En Zabbix los nombres de template son únicos en toda la instancia, y somos muchos en la misma.

✅ **Checkpoint 0:** estás dentro de Zabbix y ves tu host `ccossNN` en *Data collection → Hosts*.

---

## Parte 1 · El mapa: dónde se contribuye a Zabbix

| Qué | Dónde | ¿Para empezar? |
|---|---|---|
| Código del servidor, agente y frontend (C, Go, PHP) | https://git.zabbix.com (espejo en https://github.com/zabbix/zabbix) | Avanzado: parches vía JIRA y Contributor Agreement |
| Bugs y propuestas | https://support.zabbix.com | ✅ Sí: un buen reporte vale oro |
| Templates oficiales | carpeta `templates/` del repo principal | Revisión del equipo de Zabbix |
| **Templates de la comunidad** | https://github.com/zabbix/community-templates | ✅ **Sí: lo que haremos hoy** |
| Traducciones de la interfaz | https://translate.zabbix.com | ✅ Sí, no requiere código |
| Documentación | https://www.zabbix.com/documentation | Reportes y sugerencias vía JIRA |
| Plugins de Zabbix Agent 2 | Go, SDK en https://git.zabbix.com | Intermedio |
| Integraciones (webhooks) | JavaScript dentro de Zabbix | Intermedio |
| Foro y comunidad | https://www.zabbix.com/forum | ✅ Responder preguntas también es contribuir |

**¿Qué es un template?** Un archivo YAML que le dice a Zabbix *qué medir*, *cómo interpretarlo* y *cuándo alertar* sobre una tecnología. Lo enlazas a un host y listo: no se configura nada a mano. Hay más de 300 oficiales y cientos de la comunidad.

---

## Parte 2 · Construimos el template (45 min)

Vamos a monitorear el **clima actual de Mérida** con la API gratuita de [Open-Meteo](https://open-meteo.com), que no necesita registro ni clave.

Abre esta URL en otra pestaña para ver qué devuelve la API:

```
https://api.open-meteo.com/v1/forecast?latitude=20.97&longitude=-89.62&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,uv_index&timezone=auto
```

```json
{
  "latitude": 20.98,
  "longitude": -89.63,
  "current": {
    "time": "2026-11-13T13:00",
    "temperature_2m": 32.5,
    "relative_humidity_2m": 55,
    "apparent_temperature": 37.4,
    "precipitation": 0.0,
    "weather_code": 0,
    "wind_speed_10m": 10.1,
    "uv_index": 3.1
  }
}
```

La idea central: **una sola consulta** a la API (item *maestro*) y varios **items dependientes** que sacan cada dato de ese JSON. Así no hacemos 7 llamadas a la API, sino una.

### 2.1 · Crear el template

*Data collection → Templates → Create template*

| Campo | Valor |
|---|---|
| Template name | `Open-Meteo by HTTP - ccossNN` |
| Template groups | `CCOSS 2026/ccossNN` |
| Description | `Monitors current weather conditions using the Open-Meteo API.` |

Pestaña **Tags**:

| Name | Value |
|---|---|
| `class` | `software` |
| `target` | `open-meteo` |

Pestaña **Macros**:

| Macro | Value | Description |
|---|---|---|
| `{$OPENMETEO.LATITUDE}` | `20.97` | Latitude of the monitored location. |
| `{$OPENMETEO.LONGITUDE}` | `-89.62` | Longitude of the monitored location. |
| `{$OPENMETEO.TEMP.APPARENT.MAX.WARN}` | `40` | Warning threshold of the apparent temperature, in °C. |
| `{$OPENMETEO.WIND.SPEED.MAX.WARN}` | `50` | Warning threshold of the wind speed, in km/h. |

Pulsa **Add**.

> 💡 **¿Por qué así?** Las [guías de templates de Zabbix](https://www.zabbix.com/documentation/guidelines/en/template_guidelines) piden: nombre que termina con el método de recolección (*by HTTP*), tags `class` y `target`, y **ningún umbral fijo**: todo umbral va en una macro con sufijo `.WARN`/`.CRIT`, para que cada usuario lo ajuste sin editar el template.

### 2.2 · El item maestro (HTTP agent)

Abre tu template → *Items* → *Create item*

| Campo | Valor |
|---|---|
| Name | `Weather: Get current conditions` |
| Type | `HTTP agent` |
| Key | `openmeteo.current.get` |
| Type of information | `Text` |
| URL | `https://api.open-meteo.com/v1/forecast` |
| Query fields | `latitude` = `{$OPENMETEO.LATITUDE}`<br>`longitude` = `{$OPENMETEO.LONGITUDE}`<br>`current` = `temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,uv_index`<br>`timezone` = `auto` |
| Update interval | `15m` |
| History | `Do not store` |
| Description | `Master item: raw JSON with the current conditions from the Open-Meteo API.` |
| Tags (pestaña **Tags**) | `component` = `raw` |

Antes de guardar, pulsa **Test** → **Get value and test**. Deberías ver el JSON. 🎉

> 💡 El maestro no guarda historia (`Do not store`): solo alimenta a los dependientes. Así se ahorra espacio en la base de datos.

✅ **Checkpoint 1:** el botón *Test* te devuelve el JSON de Open-Meteo.

### 2.3 · Items dependientes

*Create item* para cada uno. Cada item se completa en **tres pestañas**:

1. Pestaña **Item**
   - **Type:** `Dependent item`
   - **Master item:** `Weather: Get current conditions`
   - **Type of information:** `Numeric (float)`
   - **Name**, **Key**, **Units** y **Description**: de la tabla de abajo
2. Pestaña **Tags** → `component` = `environment`
3. Pestaña **Preprocessing** → *Add* → `JSONPath` → la ruta de la tabla

> ⚠️ **No olvides la pestaña Tags.** Es lo que más se olvida, y la revisión automática del PR lo marca como error.

| Name | Key | Units | JSONPath | Description |
|---|---|---|---|---|
| `Weather: Temperature` | `openmeteo.temperature` | `°C` | `$.current.temperature_2m` | `Air temperature at 2 meters above ground.` |
| `Weather: Apparent temperature` | `openmeteo.temperature.apparent` | `°C` | `$.current.apparent_temperature` | `Apparent ("feels like") temperature, combining air temperature, humidity and wind.` |
| `Weather: Relative humidity` | `openmeteo.humidity` | `%` | `$.current.relative_humidity_2m` | `Relative humidity at 2 meters above ground, in %.` |
| `Weather: Wind speed` | `openmeteo.wind.speed` | `km/h` | `$.current.wind_speed_10m` | `Wind speed at 10 meters above ground, in km/h.` |

> ⚡ Truco: crea el primero completo (con su tag), ábrelo y usa **Clone** para los demás. El clon conserva el tag; solo cambias nombre, key, unidades, descripción y JSONPath.

> 💡 Nombres `Recurso: Métrica` en *sentence case*, keys en minúsculas con puntos, y unidades en el campo *Units* (nunca dentro del nombre). Es lo que pide la guía, y es lo primero que mira un revisor.

✅ **Checkpoint 2:** tienes 5 items en el template (1 maestro + 4 dependientes). En la lista de items, la columna *Tags* muestra `component: environment` en los 4 dependientes.

### 2.4 · Value map: de números a palabras

Open-Meteo devuelve el estado del cielo como un código WMO (`0` = despejado, `61` = lluvia ligera, `95` = tormenta…).

1. En tu template, pestaña **Value mapping** → *Add*:
   - Name: `WMO weather code`
   - Mappings: `0` → `Clear sky`, `1` → `Mainly clear`, `2` → `Partly cloudy`, `3` → `Overcast`, `61` → `Slight rain`, `63` → `Moderate rain`, `65` → `Heavy rain`, `95` → `Thunderstorm`
2. Nuevo item dependiente:

| Campo | Valor |
|---|---|
| Name | `Weather: Weather condition` |
| Key | `openmeteo.weather.code` |
| Type of information | `Numeric (unsigned)` |
| Value mapping | `WMO weather code` |
| Description | `Current weather condition as a WMO weather code.` |
| Tags (pestaña **Tags**) | `component` = `environment` |
| Preprocessing | 1. `JSONPath` = `$.current.weather_code`<br>2. `Discard unchanged with heartbeat` = `6h` |

> 💡 *Discard unchanged with heartbeat* evita guardar el mismo valor cada 15 minutos si el cielo no cambia, pero guarda al menos uno cada 6 h.

### 2.5 · Triggers: cuándo alertar

*Triggers → Create trigger*

**Trigger 1: calor**

| Campo | Valor |
|---|---|
| Name | `Weather: High apparent temperature` |
| Event name | `Weather: High apparent temperature (over {$OPENMETEO.TEMP.APPARENT.MAX.WARN}°C for 30m)` |
| Operational data | `Feels like: {ITEM.LASTVALUE1}` |
| Severity | `Warning` |
| Expression | `min(/Open-Meteo by HTTP - ccossNN/openmeteo.temperature.apparent,30m)>{$OPENMETEO.TEMP.APPARENT.MAX.WARN}` |
| Tags | `scope` = `notice` |

**Trigger 2: viento**

| Campo | Valor |
|---|---|
| Name | `Weather: Strong wind` |
| Severity | `Average` |
| Expression | `min(/Open-Meteo by HTTP - ccossNN/openmeteo.wind.speed,30m)>{$OPENMETEO.WIND.SPEED.MAX.WARN}` |
| Tags | `scope` = `notice` |

> 💡 **¿Por qué `min(...,30m)` y no `last(...)`?** Si solo miras el último valor, un pico de un minuto dispara una alerta y despierta a alguien a las 3 a. m. Con `min` durante 30 minutos, la alerta salta solo si *todo* ese tiempo estuvo por encima del umbral.

> 💡 El nombre del problema dice **qué** pasa; el umbral va en *Event name* y el valor actual en *Operational data*. Nunca `{ITEM.LASTVALUE}` en el nombre.

✅ **Checkpoint 3:** tu template tiene 6 items, 1 value map y 2 triggers.

### 2.6 · Verlo funcionar

1. *Data collection → Hosts* → abre `ccossNN` → **Templates** → *Link new templates* → el tuyo → *Update*.
2. *Data collection → Hosts → ccossNN → Items* → marca `Weather: Get current conditions` → **Execute now**.
3. *Monitoring → Latest data* → filtra por tu host. Ahí está el clima de Mérida. 🌴

**Forzar una alerta:** en tu host, pestaña *Macros* → *Inherited and host macros* → cambia `{$OPENMETEO.TEMP.APPARENT.MAX.WARN}` a `20` → *Update*. Como el trigger mira 30 minutos, para la demo cambia temporalmente `30m` por `1m` en la expresión y vuelve a ejecutar el maestro. Mira *Monitoring → Problems*.

> Esto es justo para lo que sirven las macros: el template no se toca, solo se ajusta el valor en el host. Recuerda volver a poner `30m` antes de exportar.

**Bonus:** cambia las coordenadas de tu host a tu ciudad natal.

✅ **Checkpoint 4:** ves datos en *Latest data* y un problema en *Problems*.

---

## Parte 3 · Del template al Pull Request (30 min)

### 3.1 · Exportar

*Data collection → Templates* → marca tu template → **Export → YAML**. Se descarga `zbx_export_templates.yaml`.

Ábrelo con cualquier editor de texto (o directamente en GitHub en el siguiente paso):

1. Reemplaza todas las apariciones de ` - ccossNN` por nada, para que quede `Open-Meteo by HTTP`. Ojo: aparece también dentro de las expresiones de los triggers.
2. Cambia el grupo `CCOSS 2026/ccossNN` por `Templates/Applications`.
3. Guárdalo como `template_open_meteo_http.yaml`.

> ⚠️ El nombre del archivo en tu computadora es **solo** `template_open_meteo_http.yaml`, sin carpetas ni `/`. Las carpetas se crean después en GitHub. En Mac, un `/` en el nombre de un archivo se convierte en `:` y GitHub termina creando un archivo llamado `participantes:usuario:...`.

> 💡 Mira el YAML: es texto plano, versionable, revisable línea por línea en un PR. Eso es "monitoreo como código".

### 3.2 · El README

Todo template se entrega con un `README.md`. Crea uno con esta estructura mínima:

```markdown
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
```

### 3.3 · Fork y Pull Request (todo desde el navegador)

Hoy enviamos el PR a un **repositorio de práctica**, no al repo oficial: 40 PRs idénticos con el clima de Mérida no le hacen ningún favor a los mantenedores. 😉

Ten a mano los dos archivos: `template_open_meteo_http.yaml` (3.1) y el texto del README (3.2).

**1 · Fork.** Abre **https://github.com/fvilarnovo/ccoss-2026-taller-zabbix** → botón **Fork** (arriba a la derecha) → *Create fork*. Ahora tienes una copia en `github.com/<tu-usuario>/ccoss-2026-taller-zabbix`. Todo lo que sigue se hace **en tu fork**.

**2 · Crear el README y tu rama.**
- *Add file → Create new file*.
- En el nombre escribe `participantes/<tu-usuario-github>/README.md`. Cada `/` que escribes crea una carpeta: vas a ver cómo se arma la ruta.
- Pega el README.
- *Commit changes…* → elige **Create a new branch for this commit and start a pull request** → nómbrala `mi-template` → *Propose changes*.
- GitHub te lleva a la pantalla *Open a pull request*. **Todavía no lo crees**: primero falta el template. Vuelve a la página de tu fork.

**3 · Subir el template.**
- Arriba a la izquierda, en el selector que dice `main`, elige **`mi-template`**.
- Entra a `participantes/<tu-usuario-github>/`.
- *Add file → Upload files* → arrastra `template_open_meteo_http.yaml`.
- *Commit changes*, elige **Commit directly to the `mi-template` branch**.

**4 · Abrir el Pull Request.**
- Aparece un aviso amarillo: *"mi-template had recent pushes"* → **Compare & pull request**. Si no aparece: pestaña *Pull requests → New pull request*.
- Revisa la línea de arriba: **base repository** `fvilarnovo/ccoss-2026-taller-zabbix`, **base** `main` ← **head repository** `<tu-usuario>/ccoss-2026-taller-zabbix`, **compare** `mi-template`.
- En *Files changed* deben aparecer **solo 2 archivos**, los dos dentro de `participantes/<tu-usuario-github>/`.
- Título: `Add Open-Meteo by HTTP template (<tu-usuario>)`. En la descripción, cuenta qué hace y cómo lo probaste.
- **Create pull request**.

**5 · Revisión automática.**
- En el PR aparece el check **Revisión del template**. Tarda unos 30 segundos.
- Si sale ❌: *Details* → abre el paso *Revisar templates modificados* y lee los mensajes. Los ❌ son obligatorios; los 💡 son sugerencias.
- Para corregir: si el error es del template (por ejemplo, falta un tag), corrígelo en Zabbix y vuelve a exportar. Luego, en tu fork, en la rama `mi-template`, abre el archivo → ícono de lápiz (o *Upload files* de nuevo con el mismo nombre) → *Commit directly to the `mi-template` branch*. El PR se vuelve a revisar solo.

> ¿Prefieres la terminal? `git clone` de tu fork, `git checkout -b mi-template`, copia los archivos, `git add`, `git commit`, `git push` y abre el PR desde GitHub. Es lo mismo.

✅ **Checkpoint 5:** tienes un PR abierto con el check en verde.

### 3.4 · La revisión

Los instructores van a comentar algunos PRs en vivo. Lo que un revisor de templates suele pedir:

- ¿El nombre termina con el método (*by HTTP*)? ¿Tiene tags `class` y `target`?
- ¿Cada item tiene descripción, unidades y tag `component`? ¿Cada trigger tiene tag `scope`?
- ¿Hay umbrales fijos en las expresiones en vez de macros?
- ¿Los triggers usan `min/max` en una ventana para no ser ruidosos?
- ¿El README explica cómo configurarlo y lista las macros?
- ¿Se dejó algo de prueba (como `1m` en vez de `30m`)?

Cuando te comenten: responde, corrige en la misma rama y marca la conversación como *Resolved*. **Una review no es un rechazo**: es la forma normal de trabajar en open source.

---

## Parte 4 · Otras puertas para contribuir (15 min)

**Reportar un bug que sirva** (https://support.zabbix.com): versión exacta, pasos para reproducir, resultado esperado vs. obtenido, logs o capturas. Busca antes si ya existe.

**Traducir Zabbix al español** (https://translate.zabbix.com): crea tu cuenta, elige *Spanish* y revisa o propone cadenas. Hay muchas sin traducir o sin revisar.

**Plugin de Zabbix Agent 2 en Go:** el agente 2 se extiende con plugins cargables. Es una buena forma de aprender Go con un proyecto real. Empieza por la documentación de *Plugins* y el ejemplo del SDK.

**Integración por webhook en JavaScript:** *Alerts → Media types* tiene decenas de integraciones (Telegram, Slack, Teams…). Cada una es un pequeño script JavaScript. ¿Falta la herramienta que usa tu comunidad? Ahí tienes tu contribución.

**Un template de verdad para la comunidad:** piensa en algo que tú o tu escuela usen y que no tenga template: una API pública de tu ciudad, un servicio open source, un dispositivo. Ese sí va a https://github.com/zabbix/community-templates (lee su `README` y `CONTRIBUTING` antes).

---

## Parte 5 · Para seguir

- Template de referencia completo, con dashboard: https://github.com/fvilarnovo/ccoss-2026-taller-zabbix/tree/main/referencia
- Guías de templates: https://www.zabbix.com/documentation/guidelines/en/template_guidelines
- Manual de Zabbix: https://www.zabbix.com/documentation/current/es/manual
- Zabbix en tu máquina, con Docker: https://www.zabbix.com/documentation/current/es/manual/installation/containers
- Foro: https://www.zabbix.com/forum

> ⚠️ Tu usuario de Zabbix Cloud se elimina al terminar el evento. Si quieres conservar tu trabajo, exporta tu template (ya lo hiciste en la parte 3 😉).

¡Gracias por participar! Si abres un PR a community-templates en las próximas semanas, etiquétanos: lo revisamos con gusto.
