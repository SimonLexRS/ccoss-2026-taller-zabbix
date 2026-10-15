#!/usr/bin/env python3
"""Revisión automática de los templates del taller (subconjunto de las guías de Zabbix).

  python3 scripts/check_template.py participantes/<usuario>/template_*.yaml

Errores (❌) hacen fallar el check; sugerencias (💡) no.
"""
import os
import re
import sys

import yaml

errors, hints = [], []


def err(msg):
    errors.append(msg)


def hint(msg):
    hints.append(msg)


def check(path):
    try:
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:  # noqa: BLE001
        return err(f"{path}: no es un YAML válido ({e})")
    exp = (doc or {}).get("zabbix_export")
    if not exp:
        return err(f"{path}: falta la clave raíz `zabbix_export`. ¿Exportaste desde Zabbix en formato YAML?")
    if not os.path.exists(os.path.join(os.path.dirname(path), "README.md")):
        err("Falta README.md en la misma carpeta que el template.")
    for t in exp.get("templates", []):
        name = t.get("template", "")
        if re.search(r"ccoss\d+", name, re.I):
            err(f"El nombre `{name}` todavía tiene tu sufijo del taller; quítalo (también en las expresiones de los triggers).")
        if not re.search(r" by (HTTP|SNMP|Zabbix agent( 2| active)?|Script|ODBC|JMX|IPMI)$", name):
            err(f"El nombre `{name}` debe terminar con el método de recolección, por ejemplo `by HTTP`.")
        tags = {(g.get("tag"), g.get("value")) for g in t.get("tags", [])}
        if not any(k == "class" for k, _ in tags):
            err("El template necesita un tag `class` (por ejemplo `class: software`).")
        if not any(k == "target" for k, _ in tags):
            err("El template necesita al menos un tag `target` (por ejemplo `target: open-meteo`).")
        if not t.get("description"):
            hint("Agrega una descripción al template: es lo primero que lee quien lo importa.")
        for g in t.get("groups", []):
            if g.get("name", "").startswith("CCOSS"):
                hint(f"El grupo `{g['name']}` es del taller; en la comunidad se usa `Templates/<categoría>`.")
        for item in t.get("items", []):
            iname = item.get("name", "")
            if not re.match(r"^[^:]+: ", iname):
                err(f"Item `{iname}`: el nombre debe empezar con el recurso, por ejemplo `Weather: Temperature`.")
            if item.get("key", "") != item.get("key", "").lower():
                err(f"Item `{iname}`: la key debe ir en minúsculas.")
            if not any(g.get("tag") == "component" for g in item.get("tags", [])):
                err(f"Item `{iname}`: falta el tag `component`.")
            if not item.get("description"):
                hint(f"Item `{iname}`: agrega una descripción.")
            if item.get("type") == "HTTP_AGENT" and str(item.get("history", "")) != "0":
                hint(f"Item `{iname}`: un item maestro no necesita guardar historia (History: Do not store).")
            for tr in item.get("triggers", []):
                check_trigger(tr)
        for tr in exp.get("triggers", []):
            check_trigger(tr)


def check_trigger(tr):
    tname, expr = tr.get("name", ""), tr.get("expression", "")
    if "{ITEM.LASTVALUE" in tname:
        err(f"Trigger `{tname}`: no pongas valores en el nombre; usa *Operational data*.")
    if not any(g.get("tag") == "scope" for g in tr.get("tags", [])):
        err(f"Trigger `{tname}`: falta el tag `scope`.")
    if tr.get("priority") == "DISASTER":
        hint(f"Trigger `{tname}`: la severidad Disaster no se usa en templates.")
    if re.search(r"[<>]=?\s*\d", expr) and "nodata(" not in expr and "{$" not in expr:
        hint(f"Trigger `{tname}`: el umbral está fijo en la expresión; ¿podría ser una macro {{$...WARN}}?")
    if re.search(r",\s*1m\)", expr):
        hint(f"Trigger `{tname}`: ventana de 1m. ¿Quedó de la prueba? La referencia usa 30m.")


def main():
    files = [f for f in sys.argv[1:] if f.endswith((".yaml", ".yml"))]
    if not files:
        print("No hay templates YAML en este PR.")
        return 0
    for f in files:
        check(f)
    for h in hints:
        print(f"💡 {h}")
    for e in errors:
        print(f"❌ {e}")
    if errors:
        print(f"\n{len(errors)} error(es). Corrige en tu rama y el PR se vuelve a revisar solo.")
        return 1
    print(f"\n✅ Todo en orden ({len(hints)} sugerencia(s)). Ahora espera la revisión humana.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
