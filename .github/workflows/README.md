# Guía de workflows

Cada archivo `.yml` de esta carpeta es un workflow: GitHub lo ejecuta cuando ocurre su *disparador* (`on:`).

| Workflow | Disparador | Para qué sirve | ¿Cuándo lo necesito? |
| --- | --- | --- | --- |
| `tests.yml` | push, PR | Ejecuta pytest | Siempre |
| `lint.yml` | push, PR | Ruff (calidad + formato) | Siempre |
| `validate.yml` | push, PR, **diario** | hassfest + HACS | Siempre en integraciones HA |
| `codeql.yml` | push/PR a main, semanal | Seguridad (SAST) | Repos públicos |
| `dependency-review.yml` | PR | Bloquea dependencias vulnerables | Si aceptas PRs |
| `release.yml` | tag `vX.Y.Z` | Publica la release (zip + changelog) | Al sacar versión |
| `release-drafter.yml` | push a main | Borrador de changelog por etiquetas | Opcional |
| `stale.yml` | diario | Cierra issues/PRs sin actividad | Cuando haya volumen |
| `../dependabot.yml` | semanal | PRs de actualización de dependencias | Siempre |

## Conceptos clave

- **Disparadores (`on:`)**: `push`, `pull_request`, `schedule` (cron), `workflow_dispatch`
  (botón manual), `release`, `workflow_run` (encadenar workflows).
- **`permissions:`** limita lo que puede hacer el token del workflow. Pon lo mínimo.
- **`concurrency:`** evita ejecuciones duplicadas del mismo workflow.
- **Cron programado** sirve para detectar roturas externas (cambios en HA/HACS) sin commits.
- Las versiones `@v4` de las acciones las mantiene Dependabot.

## Pasos manuales en GitHub

1. *Settings → Branches*: protege `main` y marca como obligatorios `pytest`, `ruff`, `Hassfest` y `HACS`.
2. *Settings → Code security*: activa Dependabot alerts y Code scanning.
3. Etiquetas `bug`, `enhancement`, `dependencies`, `github_actions` (las usan stale, dependabot y release-drafter).
4. Para HACS: añade descripción y topics al repo (`home-assistant`, `hacs`, ...).

## Publicar una versión

```bash
# 1. sube "version" en custom_components/murcia_tram/manifest.json
git tag v0.2.0 && git push origin v0.2.0
```
