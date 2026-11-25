# Murcia Tram

[![Marketplace](https://img.shields.io/badge/Home%20Assistant-Marketplace-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/)
[![Validate](https://github.com/procamora/murcia_tram/actions/workflows/validate.yml/badge.svg)](https://github.com/procamora/murcia_tram/actions/workflows/validate.yml)
[![Tests](https://github.com/procamora/murcia_tram/actions/workflows/tests.yml/badge.svg)](https://github.com/procamora/murcia_tram/actions/workflows/tests.yml)

Integración para Home Assistant que muestra cuántos minutos faltan para que pasen los
tranvías por una parada del **Tranvía de Murcia**, en cada sentido. Eliges una parada y
listo: así sabes cuándo salir de casa.

> **Aviso:** proyecto no oficial, sin relación con la Sociedad Concesionaria Tranvía de
> Murcia. Usa los mismos datos que muestra la ficha de cada parada en
> [tranviademurcia.es](https://tranviademurcia.es/). Si la web cambia, puede dejar de
> funcionar hasta que se actualice.

## Qué crea

Por cada sentido de la parada, dos sensores con los minutos que faltan:

- **Próximo tranvía a _destino_**
- **Siguiente tranvía a _destino_**

Ejemplo para La Ladera:

| Entidad | Estado |
| --- | --- |
| `sensor.la_ladera_proximo_tranvia_a_universidades` | 7 min |
| `sensor.la_ladera_siguiente_tranvia_a_universidades` | 17 min |
| `sensor.la_ladera_proximo_tranvia_a_nueva_condomina` | 2 min |
| `sensor.la_ladera_siguiente_tranvia_a_nueva_condomina` | 6 min |

- Atributos: línea, número de tranvía y vía.
- Se actualiza cada minuto, igual que la web oficial.
- De madrugada, sin servicio, los sensores quedan *no disponibles* y vuelven solos.
- Puedes añadir varias paradas (cada una es un dispositivo).

Los identificadores exactos dependen del idioma de tu Home Assistant; los tienes en
*Ajustes → Dispositivos y servicios → Murcia Tram*.

## Instalación

### Marketplace (Home Assistant 2026.11 o posterior)

1. *Ajustes → Marketplace → Añadir desde enlace*.
2. Escribe `procamora/murcia_tram`.
3. Abre **Murcia Tram**, pulsa **Instalar** y reinicia si te lo pide.

### HACS (Home Assistant anterior a 2026.11)

1. HACS → menú ⋮ → *Repositorios personalizados*.
2. Añade `https://github.com/procamora/murcia_tram` con categoría **Integración**.
3. Busca **Murcia Tram**, descárgala y reinicia.

### Manual

Copia `custom_components/murcia_tram` en la carpeta `custom_components` de tu
configuración y reinicia.

## Configuración

*Ajustes → Dispositivos y servicios → Añadir integración → Murcia Tram* y elige la parada.
La más cercana a tu casa aparece ya seleccionada.

## Tarjetas de ejemplo

Tarjetas nativas, no hace falta instalar nada más:

```yaml
type: grid
columns: 2
square: false
cards:
  - type: tile
    entity: sensor.la_ladera_proximo_tranvia_a_universidades
    name: → Universidades
  - type: tile
    entity: sensor.la_ladera_proximo_tranvia_a_nueva_condomina
    name: → Nueva Condomina
  - type: tile
    entity: sensor.la_ladera_siguiente_tranvia_a_universidades
    name: Siguiente
  - type: tile
    entity: sensor.la_ladera_siguiente_tranvia_a_nueva_condomina
    name: Siguiente
```

Versión compacta con Markdown:

```yaml
type: markdown
title: 🚋 La Ladera
content: >-
  {% macro t(e) -%}
  {{- (states(e) ~ ' min') if has_value(e) else '—' -}}
  {%- endmacro %}
  **Hacia Universidades:** {{ t('sensor.la_ladera_proximo_tranvia_a_universidades') }}
  · luego {{ t('sensor.la_ladera_siguiente_tranvia_a_universidades') }}

  **Hacia Nueva Condomina:** {{ t('sensor.la_ladera_proximo_tranvia_a_nueva_condomina') }}
  · luego {{ t('sensor.la_ladera_siguiente_tranvia_a_nueva_condomina') }}
```

## Aviso para salir de casa

Si tardas 6 minutos andando hasta la parada, esta automatización te avisa cuando el
próximo tranvía hacia el centro esté a 8 minutos (2 de margen):

```yaml
alias: Hora de salir al tranvía
triggers:
  - trigger: numeric_state
    entity_id: sensor.la_ladera_proximo_tranvia_a_universidades
    below: 9
conditions:
  - condition: time
    after: "07:30:00"
    before: "09:00:00"
    weekday: [mon, tue, wed, thu, fri]
actions:
  - action: notify.notify
    data:
      message: >-
        Sal ya: el tranvía a Universidades pasa por La Ladera en
        {{ states(trigger.entity_id) }} min
```

## Cómo funciona

La web oficial consulta, para cada parada:

- `GET https://tranviademurcia.es/api-horarios/get_paradas`: lista de paradas (`saeid` es el
  identificador del servicio de tiempo real).
- `POST https://tranviademurcia.es/webservicecall.php` con `idParada=<saeid>&via=0`: XML con
  los dos próximos tranvías de cada sentido.

La integración hace esas mismas peticiones, una por parada y minuto. No reduzcas el
intervalo: es un servicio público y gratuito.

## Uso de los datos

- Este repositorio solo contiene código. No incluye, guarda ni redistribuye datos del
  Tranvía de Murcia: cada instalación consulta la web oficial directamente, igual que lo
  haría un navegador. Los datos de los tests son inventados.
- Los datos pertenecen a la Sociedad Concesionaria Tranvía de Murcia, S.A. y su uso está
  sujeto al [aviso legal de tranviademurcia.es](https://tranviademurcia.es/aviso-legal/),
  que solo permite un uso privado y personal, no comercial.
- Si representas a Tranvía de Murcia y quieres que se cambie algo en este proyecto, abre una
  incidencia o escribe al autor y se atenderá.

## Desarrollo

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
ruff check . && pytest
```

`custom_components/murcia_tram/api.py` no depende de Home Assistant.

---

## English

Home Assistant integration that shows the minutes until the next two trams in each
direction at a **Murcia tram** (Spain) stop. Install it from *Settings → Marketplace → Add
from link* (`procamora/murcia_tram`), add the integration and pick a stop. It polls the
same public endpoints the operator's website uses, once per minute. Not affiliated with
Tranvía de Murcia. The MIT license covers this code only; the data belongs to Tranvía de
Murcia and is subject to its legal notice (private, non-commercial use).

## Licencia

El código se publica bajo licencia MIT (ver `LICENSE`). La licencia cubre solo el código de
este repositorio: no da ningún derecho sobre los datos, el nombre ni la marca de Tranvía de
Murcia, que pertenecen a su titular.
