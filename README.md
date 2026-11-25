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

Todas son nativas de Home Assistant: no hace falta instalar nada. Para añadirlas:
*Editar panel → Añadir tarjeta → Manual* y pega el YAML.

Los ejemplos usan los IDs de una instalación en español para la parada La Ladera
(`sensor.la_ladera_proximo_tranvia_a_universidades`…). En inglés serían
`sensor.la_ladera_next_tram_to_universidades` y `sensor.la_ladera_following_tram_to_…`.
Comprueba los tuyos en *Ajustes → Dispositivos y servicios → Murcia Tram* y sustitúyelos.

Las tarjetas 1 y 2 suponen que tardas **6 minutos andando** hasta la parada y quieres
**2 minutos de margen**. Ajusta `walk` y `margin` en la tarjeta 1 y los cortes `from: 6` /
`from: 8` en la 2.

### 1. ¿Cuándo salgo?

Por cada sentido te dice si te da tiempo (*Sal en X min*), si tienes que salir ya, o si
pierdes el próximo y cuándo salir para el siguiente.

```yaml
type: markdown
title: 🚋 ¿Cuándo salgo?
content: |
  {%- set walk = 6 -%}{#- minutos andando de casa a la parada -#}
  {%- set margin = 2 -%}{#- con menos holgura que esto, «sal ya» -#}
  {%- set dirs = [
    ('Universidades', 'sensor.la_ladera_proximo_tranvia_a_universidades', 'sensor.la_ladera_siguiente_tranvia_a_universidades'),
    ('Nueva Condomina', 'sensor.la_ladera_proximo_tranvia_a_nueva_condomina', 'sensor.la_ladera_siguiente_tranvia_a_nueva_condomina'),
  ] -%}
  {%- for name, e1, e2 in dirs %}
  {%- set n1 = states(e1) | int(-1) %}
  {%- set n2 = states(e2) | int(-1) %}
  {%- if n1 < 0 %}
  <ha-alert alert-type="info"><b>→ {{ name }}:</b> Sin servicio ahora mismo</ha-alert>
  {%- elif n1 - walk >= margin %}
  <ha-alert alert-type="success"><b>→ {{ name }}:</b> Sal en {{ n1 - walk }} min · pasa en {{ n1 }} min</ha-alert>
  {%- elif n1 >= walk %}
  <ha-alert alert-type="warning"><b>→ {{ name }}:</b> ¡Sal ya! Pasa en {{ n1 }} min</ha-alert>
  {%- elif n2 >= walk %}
  <ha-alert alert-type="error"><b>→ {{ name }}:</b> A este no llegas ({{ n1 }} min). Para el siguiente sal en {{ n2 - walk }} min</ha-alert>
  {%- else %}
  <ha-alert alert-type="error"><b>→ {{ name }}:</b> No llegas a los próximos ({{ n1 }} y {{ n2 if n2 >= 0 else '—' }} min)</ha-alert>
  {%- endif %}
  {%- endfor %}
```

### 2. Semáforo

Un reloj por sentido: rojo si no llegas, naranja si tienes que salir ya, verde si te da
tiempo.

```yaml
type: grid
columns: 2
square: false
cards:
  - type: gauge
    entity: sensor.la_ladera_proximo_tranvia_a_universidades
    name: → Universidades
    unit: min
    min: 0
    max: 20
    needle: true
    segments:
      - from: 0
        color: "#db4437"
      - from: 6
        color: "#ffa600"
      - from: 8
        color: "#43a047"
  - type: gauge
    entity: sensor.la_ladera_proximo_tranvia_a_nueva_condomina
    name: → Nueva Condomina
    unit: min
    min: 0
    max: 20
    needle: true
    segments:
      - from: 0
        color: "#db4437"
      - from: 6
        color: "#ffa600"
      - from: 8
        color: "#43a047"
```

### 3. Tabla compacta

Próximo, siguiente y número de tranvía de cada sentido.

```yaml
type: markdown
title: 🚋 La Ladera
content: |
  {%- macro t(e) -%}{{ (states(e) ~ ' min') if has_value(e) else '—' }}{%- endmacro %}
  | Sentido | Próximo | Siguiente | Tranvía |
  |:--|:-:|:-:|:-:|
  | → Universidades | **{{ t('sensor.la_ladera_proximo_tranvia_a_universidades') }}** | {{ t('sensor.la_ladera_siguiente_tranvia_a_universidades') }} | {{ state_attr('sensor.la_ladera_proximo_tranvia_a_universidades', 'vehicle') or '—' }} |
  | → Nueva Condomina | **{{ t('sensor.la_ladera_proximo_tranvia_a_nueva_condomina') }}** | {{ t('sensor.la_ladera_siguiente_tranvia_a_nueva_condomina') }} | {{ state_attr('sensor.la_ladera_proximo_tranvia_a_nueva_condomina', 'vehicle') or '—' }} |
```

### 4. Tiles con modo noche

Las cuatro tarjetas de siempre, que de madrugada se sustituyen por un único aviso de
«sin servicio».

```yaml
type: vertical-stack
cards:
  - type: conditional
    conditions:
      - condition: state
        entity: sensor.la_ladera_proximo_tranvia_a_universidades
        state_not: unavailable
    card:
      type: grid
      columns: 2
      square: false
      cards:
        - type: tile
          entity: sensor.la_ladera_proximo_tranvia_a_universidades
          name: → Universidades
          icon: mdi:tram
        - type: tile
          entity: sensor.la_ladera_proximo_tranvia_a_nueva_condomina
          name: → Nueva Condomina
          icon: mdi:tram
        - type: tile
          entity: sensor.la_ladera_siguiente_tranvia_a_universidades
          name: Siguiente
          icon: mdi:timer-sand
        - type: tile
          entity: sensor.la_ladera_siguiente_tranvia_a_nueva_condomina
          name: Siguiente
          icon: mdi:timer-sand
  - type: conditional
    conditions:
      - condition: state
        entity: sensor.la_ladera_proximo_tranvia_a_universidades
        state: unavailable
    card:
      type: markdown
      content: |
        <ha-alert alert-type="info"><b>La Ladera:</b> ahora mismo no hay servicio de tranvía.</ha-alert>
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

La integración hace esas mismas peticiones, una por parada y minuto, y se identifica con
el User-Agent `murcia_tram (+https://github.com/procamora/murcia_tram; ...)` para que el
operador sepa quién consulta y cómo contactar. No reduzcas el intervalo: es un servicio
público y gratuito.

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
