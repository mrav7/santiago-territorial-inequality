# Lakehouse Execution Tracker — Santiago Territorial Inequality ETL

**Proyecto:** Santiago Territorial Inequality ETL · Databricks Lakehouse  
**Versión del tracker:** 1.0  
**Fecha de corte:** 2026-09-25  
**Estado:** LISTO PARA ADOPCIÓN  
**Repositorio vigente:** `mrav7/santiago-territorial-inequality`  
**HEAD remoto revisado:** `e9a8c4cda7d4b7f79bd291b48c9789ce86cb36ec`  
**Fuente normativa principal:** `PLAN_CANONICO_SANTIAGO_ETL_DATABRICKS_v1.0.md`  
**Metodología operativa:** `REGLA_TRABAJO_CHATGPT_CODEX_PROMPTS_REPORTS.md`

> Este tracker registra cómo ejecutar, verificar y cerrar el trabajo restante. No constituye por sí mismo evidencia de implementación. Una capability solo cambia de estado técnico cuando existe evidencia ejecutada, revisada y trazable.

---

## 1. Propósito

Mantener una vista operativa, verificable y actualizable del trabajo restante después del vertical slice de pobreza (P03–P04), sin convertir el Plan Canónico en un log mutable.

Este tracker define:

- secuencia de trabajo restante;
- dependencias y gates;
- estado operativo de cada etapa;
- acciones manuales requeridas;
- evidencia runtime que debe conservarse;
- relación entre prompt `Pxx/Cxx`, reporte `Rxx`, evidencia externa `Exx` y dictamen;
- protocolo posterior a la emisión de un reporte;
- reglas de actualización del tracker;
- riesgos y drift normativo conocido.

La prioridad permanece:

> **aprendizaje real + calidad técnica + evidencia verificable > cantidad de tecnologías**

---

## 2. Autoridad, evidencia y discrepancias

### 2.1 Orden de autoridad

1. Correcciones explícitas de Matías.
2. Estado real y vigente del repositorio para afirmar qué está implementado.
3. `PLAN_CANONICO_SANTIAGO_ETL_DATABRICKS_v1.0.md`.
4. `REGLA_TRABAJO_CHATGPT_CODEX_PROMPTS_REPORTS.md`.
5. `docs/architecture/lakehouse.md` y demás documentación vigente del repositorio.
6. Prompt canónico de la ejecución concreta (`Pxx` o `Cxx`).
7. Inferencias, siempre identificadas como tales.

El estado real del repositorio puede demostrar que una implementación difiere del plan, pero no reemplaza silenciosamente una decisión normativa. Toda discrepancia debe registrarse y resolverse explícitamente.

### 2.2 Fuentes de evidencia

Según la etapa, la evidencia puede incluir:

- branch, HEAD y `git status`;
- diff y archivos modificados;
- outputs del pipeline local;
- schemas, tablas y Volumes en Databricks;
- `DESCRIBE DETAIL`;
- `DESCRIBE HISTORY`;
- row counts;
- keys, nulls y duplicados;
- outputs de notebooks;
- consultas y resultados SQL;
- reportes `Rxx`;
- registros runtime `Exx`;
- Jobs/Workflows y sus logs;
- evidencia de Power BI;
- comparaciones contra el baseline.

### 2.3 Regla de discrepancia

Cuando norma y evidencia divergen:

1. no reconciliar silenciosamente;
2. registrar la discrepancia;
3. clasificarla como defecto, deuda, documentación desactualizada, decisión pendiente o cambio deliberado;
4. resolverla antes de convertir el estado divergente en nueva norma.

---

## 3. Estado de corte

| Etapa | Estado operativo | Estado técnico resumido |
|---|---|---|
| P00 — Baseline local | GATE_PASSED | Pipeline local y baseline preservados/validados |
| P01 — Databricks Environment Audit | GATE_PASSED | Free Edition, serverless, Unity Catalog managed y SQL Warehouse documentados |
| P02 — Lakehouse Foundation | GATE_PASSED | `workspace.bronze`, `workspace.silver`, `workspace.gold` y managed Volume validados |
| P03 — Bronze pobreza | GATE_PASSED | 351 filas, Delta managed, DQ Bronze y rerun snapshot overwrite |
| P04 — Silver pobreza + DQ + equivalencia | GATE_PASSED | 32 comunas, DQ-S01…DQ-S26 y EQ-S01…EQ-S10 PASS, `max_abs_diff = 0` |
| C04-D — estabilización de rerun Silver | READY | Correctivo previo a replicar el patrón |
| P05–P12 | PLANNED | Trabajo restante del roadmap canónico |

P04 permanece cerrado: C04-D no reescribe retrospectivamente su gate. El correctivo aborda un requisito operacional adicional detectado antes de replicar el patrón.

---

## 4. Separación entre estados operativos y estados técnicos

### 4.1 Estados operativos del tracker

Estos estados describen el avance de una **etapa de trabajo**:

- `PLANNED`: existe en el roadmap, pero su dependencia aún no está satisfecha.
- `READY`: dependencias satisfechas; el prompt puede redactarse/materializarse.
- `IN_PROGRESS`: implementación o ejecución en curso.
- `WAITING_MANUAL`: Codex terminó su ejecución y falta evidencia externa/manual.
- `UNDER_REVIEW`: existe evidencia suficiente para revisión.
- `GATE_PASSED`: el gate de la etapa fue satisfecho.
- `BLOCKED`: existe una condición que impide continuar.
- `CLOSED_WITH_LIMITATION`: la etapa se cierra de forma deliberada con una limitación explícita; no implica que la capability esté validada.

### 4.2 Estados técnicos de capabilities

Se reservan para la auditoría de capacidades y, especialmente, para P12:

- `IMPLEMENTED`
- `VALIDATED`
- `PARTIAL`
- `PLANNED`
- `NOT IMPLEMENTED`

No usar `GATE_PASSED` como sinónimo de `VALIDATED` para todas las capabilities internas de una etapa.

---

## 5. Artefactos de trazabilidad

### 5.1 Cadena mínima

Cada etapa sustancial debe dejar, como mínimo:

```text
Prompt canónico Pxx/Cxx
        ↓
Implementación + verificaciones ejecutables por Codex
        ↓
Reporte Rxx
        ↓
Evidencia runtime/manual Exx
        ↓
Revisión técnica
        ↓
APROBADO / CORREGIR / AUDITAR DE NUEVO / BLOQUEADO
        ↓
Decisión humana
        ↓
commit / merge / siguiente etapa
```

### 5.2 Reporte `Rxx`

El `Rxx` registra lo que Codex efectivamente hizo y verificó. Las acciones que dependen de Databricks, SQL Warehouse, Power BI u otro sistema externo deben quedar como `NO EJECUTADA` si Codex no las ejecutó.

El `Rxx` no se modifica retrospectivamente para simular evidencia obtenida después.

### 5.3 Evidencia runtime/manual `Exx`

Convención propuesta para evidencia persistente y sanitizada:

```text
docs/evidence/runtime/E04-D_RUNTIME.md
docs/evidence/runtime/E05_RUNTIME.md
docs/evidence/runtime/E06_RUNTIME.md
...
```

Cada `Exx` debe registrar:

- fecha y etapa;
- entorno usado;
- acción manual `Mxx-yy`;
- objeto/notebook/query ejecutado;
- resultado;
- `PASS` / `FAIL`;
- row counts y schemas relevantes;
- versiones Delta cuando apliquen;
- resultados de DQ/equivalencia;
- referencias a logs/capturas;
- limitaciones;
- responsable de la ejecución.

No todo artefacto visual debe publicarse. Se distinguen:

1. **evidencia primaria local/privada**: capturas o datos con información de cuenta/workspace;
2. **evidencia persistida en repo**: resultados sanitizados, queries, hashes, conteos y conclusiones reproducibles;
3. **evidencia pública de portfolio**: selección mínima y sanitizada.

### 5.4 Si `docs/ai/` permanece interno

La metodología de prompts/reportes puede continuar en artefactos internos/locales. El tracker y los `Exx` públicos no dependen de que `AGENTS.md`, `CLAUDE.md` o todo `docs/ai/` sean versionados.

---

## 6. Protocolo posterior a `Rxx`

Una ejecución de Codex termina al producir su `Rxx`.

Si una acción manual posterior descubre un defecto:

```text
Rxx emitido
  ↓
acción Mxx falla
  ↓
revisión = CORREGIR
  ↓
nuevo correctivo Cxx-A / Cxx-B / ...
```

Reglas:

- no reabrir el prompt original;
- no editar retrospectivamente el prompt original;
- no modificar el `Rxx` para ocultar que la falla apareció después;
- crear un correctivo más pequeño y específico;
- conservar el `Exx` con la evidencia del fallo;
- volver a ejecutar las regresiones pertinentes tras la corrección.

Si falta evidencia pero no existe un defecto demostrado, usar `AUDITAR DE NUEVO`, no inventar un bug.

---

## 7. Roadmap restante

| Orden | Prompt | Estado | Resultado principal | Gate |
|---|---|---|---|---|
| 1 | C04-D — Stabilize Silver Rerun Contract | READY | Silver pobreza reejecutable sin editar flags y sin lock al historial exacto Bronze | Patrón estable para replicar |
| 2 | P05 — Remaining Sources Bronze / Silver | PLANNED | A, B y D en Bronze/Silver con DQ, equivalencia y rerun batch | Cuatro fuentes Silver válidas |
| 3 | P06 — Gold Model + SQL + Baseline Equivalence | PLANNED | Gold dimensión/hecho + equivalencia contra CSV y SQLite | Nivel 1 / MVP |
| 4 | P07 — Lakehouse Hardening + Databricks SQL | PLANNED | Mantenibilidad, tests útiles y serving SQL | Base mantenible |
| 5 | P08 — Databricks Workflow | PLANNED | Orquestación reproducible | Nivel 2 |
| 6 | P09 — Incremental Merge + Idempotency | PLANNED | `MERGE`, insert/update y rerun lógico demostrado | Upserts e idempotencia |
| 7 | P10 — Schema Change Experiment | PLANNED | Enforcement/evolution aislados y controlados | Política de schema demostrada |
| 8 | P11 — Power BI Serving | PLANNED | Gold → SQL Warehouse → Power BI | Serving analítico o cierre con limitación |
| 9 | P12 — Final Audit + Case Study | PLANNED | Auditoría, claims y case study | Nivel 3 |

Los prompts completos P05–P12 se redactan justo antes de su ejecución usando el estado real, el reporte anterior, la evidencia vigente y las limitaciones reales del entorno.

---

# 8. Etapas detalladas

## 8.1 C04-D — Stabilize Silver Rerun Contract

**Naturaleza:** correctivo focalizado.  
**Dependencia:** P04 cerrado y tabla Silver existente.  
**Branch sugerida:** `fix/p04-silver-rerun-contract`.  
**ID propuesto:** `C04-D`; verificar antes de materializar que el identificador esté libre en el registro interno.

### Defecto confirmado D04D-01

El notebook versionado contiene una precondición que bloquea cuando la tabla Silver ya existe. El estado real documentado confirma que `workspace.silver.pobreza_ingresos` existe después de P04.

Por tanto, el notebook actual no puede ejecutar un rerun batch normal sin editar configuración/código.

### Fragilidad D04D-02

El contrato de entrada Silver exige un historial Bronze exactamente igual a `[0, 1]`. Una nueva snapshot Bronze válida puede cambiar el historial sin invalidar el estado lógico actual, haciendo fallar Silver por una condición histórica incidental.

La corrección debe validar el contrato útil del Bronze actual, no un número fijo de versiones.

### Objetivo único

Hacer que `workspace.silver.pobreza_ingresos` pueda regenerarse mediante snapshot overwrite deliberado y reproducible, manteniendo DQ/equivalencia y sin convertir la etapa en incrementalidad.

### Cambios autorizables

- reemplazar el lock exacto `EXPECTED_BRONZE_VERSIONS = [0, 1]`;
- validar propiedades necesarias del Bronze actual;
- permitir rerun cuando el target Silver existente cumple el contrato;
- bloquear si el target existente es incompatible o no puede atribuirse con seguridad;
- mantener todas las validaciones pre-write;
- mantener snapshot overwrite;
- no introducir `MERGE`.

### Fuera de alcance

- batch IDs;
- incrementalidad;
- `MERGE`;
- schema evolution;
- refactor general;
- cambios de semántica de pobreza;
- modificaciones no relacionadas.

### Reproducción/evidencia previa a la corrección

Antes de modificar, el prompt debe registrar evidencia suficiente del defecto. Cuando sea seguro y razonable:

- demostrar que la tabla Silver existe;
- demostrar que la configuración actual bloquea un rerun normal;
- registrar la condición rígida del historial Bronze.

No es necesario crear versiones Bronze artificiales solo para provocar D04D-02 si la evidencia estática y el contrato actual ya demuestran la fragilidad.

### Acciones manuales

- `M04D-01`: sincronizar/publicar el notebook corregido en Databricks.
- `M04D-02`: ejecutar `02_silver_poverty.py` con la tabla Silver ya existente.
- `M04D-03`: ejecutar `02_validate_silver_poverty.sql`.
- `M04D-04`: registrar `DESCRIBE HISTORY`, conteos, DQ y EQ en `E04-D_RUNTIME.md`.
- `M04D-05`: entregar evidencia para revisión.
- `M04D-06`: autorizar commit/push/merge solo después del dictamen.

### Gate

`C04-D = GATE_PASSED` cuando **un rerun controlado sobre el target Silver preexistente**:

- termina sin editar flags manualmente;
- conserva 32 filas y 32 keys;
- conserva 0 duplicados y 0 nulls;
- mantiene `anio_pobreza = 2022`;
- mantiene DQ/EQ en PASS;
- mantiene `max_abs_diff = 0` bajo la tolerancia vigente;
- genera una nueva versión Delta;
- no acumula filas.

No llamar a esto idempotencia incremental.

---

## 8.2 P05 — Remaining Sources Bronze / Silver

**Dependencia:** C04-D `GATE_PASSED`.  
**Branch sugerida:** `feat/remaining-sources-bronze-silver`.

### Objetivo único

Extender el patrón ya validado a:

- A — SINIM áreas verdes;
- B — SINIM capacidad municipal;
- D — Censo población.

Resultado esperado:

- las cuatro fuentes disponibles en Bronze;
- `silver.dim_comuna`;
- `silver.areas_verdes`;
- `silver.capacidad_municipal`;
- `silver.pobreza_ingresos`;
- `silver.poblacion`;
- DQ y equivalencia por fuente;
- rerun batch seguro en los nuevos verticales.

### Checkpoints internos

**P05-A — landing + Bronze SINIM A/B.** Resolver explícitamente SpreadsheetML/XML 2003. No asumir XLS binario ni añadir un conector Spark solo por apariencia.

**P05-B — Silver SINIM A/B.** Replicar reglas del baseline por `codigo_comuna`, año 2024, DQ y equivalencia.

**P05-C — Bronze/Silver Censo D.** Preservar Bronze y excluir en Silver filas/agregados fuera del grano comunal.

**P05-D — cierre transversal.** Verificar que las cuatro fuentes Silver entregan exactamente las entidades/variables necesarias para Gold.

### Condiciones para dividir P05

P05 se divide formalmente en nuevos prompts si ocurre al menos una de estas condiciones:

- A/B requieren una dependencia o parser nuevo que exige una decisión específica;
- la estrategia de ingestión SINIM difiere de forma material del patrón autorizado;
- D introduce un contrato independiente que puede avanzar de forma segura mientras A/B están bloqueadas;
- el write scope o diff deja de ser razonable para una revisión focalizada;
- una fuente queda `BLOCKED` y continuar con las otras no viola dependencias ni oculta el bloqueo.

La división requiere autorización; Codex no crea sub-prompts por su cuenta.

### Contrato de rerun batch

Por cada nueva fuente:

**Bronze**

- ejecución inicial;
- al menos un rerun snapshot controlado;
- mismo estado lógico esperado;
- nueva versión Delta;
- sin acumulación no autorizada.

**Silver**

- ejecución inicial;
- al menos un rerun sobre target válido;
- mismo conjunto esperado de keys;
- DQ/equivalencia conservadas;
- sin editar flags para permitir el rerun.

Este contrato demuestra reejecución batch, no `MERGE` ni idempotencia incremental.

### Acciones manuales

- `M05-01`: **verificar o subir** A, B y D al Volume; subir solo si faltan; comprobar siempre tamaño/hash frente al archivo versionado.
- `M05-02`: verificar o subir `dim_comuna_base.csv` y fixtures definidos por el prompt; comprobar identidad.
- `M05-03`: ejecutar Bronze A/B/D y conservar schema, row counts, metadata y Delta history.
- `M05-04`: ejecutar rerun Bronze controlado por fuente.
- `M05-05`: ejecutar Silver cuando el Bronze correspondiente haya pasado su gate.
- `M05-06`: ejecutar rerun Silver controlado por fuente.
- `M05-07`: ejecutar SQL de validación por fuente.
- `M05-08`: registrar evidencia consolidada en `E05_RUNTIME.md`.
- `M05-09`: autorizar commit/push/merge tras aprobación.

### Evidencia mínima por fuente

- identidad del archivo;
- dataset no vacío;
- Bronze Delta managed;
- metadata de ingestión;
- schema observado;
- rerun Bronze sin acumulación no autorizada;
- `codigo_comuna` resuelto en Silver;
- producto territorial de 32 comunas cuando corresponda al contrato;
- 0 duplicados por llave;
- nulls y rangos documentados;
- año esperado;
- cobertura de la dimensión maestra;
- equivalencia con baseline local;
- rerun Silver sin drift lógico.

### Gate

Las cuatro fuentes Silver reproducen las entidades/variables requeridas por el baseline y sus verticales batch son reejecutables sin diferencias materiales no explicadas.

---

## 8.3 P06 — Gold Model + SQL + Baseline Equivalence

**Dependencia:** P05 `GATE_PASSED`.  
**Branch sugerida:** `feat/gold-model`.

### Objetivo único

Construir el producto analítico Lakehouse completo y demostrar equivalencia contra los dos productos locales relevantes:

- `data/processed/desigualdad_comunal_final.csv`;
- `db/lab1_desigualdad.sqlite`.

### Gold mínimo

- `workspace.gold.dim_comuna`;
- `workspace.gold.fact_desigualdad_comunal`;
- `workspace.gold.metadata_fuentes`.

`workspace.gold.comuna_kpis` solo se crea si existe una necesidad concreta de serving.

### Comparación mínima

**Contra CSV final**

- 32 vs 32 filas;
- columnas/semántica;
- set exacto de `codigo_comuna`;
- faltantes/extras = 0;
- duplicados = 0;
- null profile;
- años;
- población;
- pobreza;
- áreas verdes;
- IPP;
- `areas_verdes_m2_hab`;
- `ipp_pesos_hab`.

**Contra SQLite**

- `dim_comuna`: 32;
- `fact_desigualdad_comunal`: 32;
- `metadata_fuentes`: 4;
- keys y atributos equivalentes;
- `nombre_comuna` en dimensión según el modelo vigente;
- fact sin duplicación no autorizada de atributos dimensionales;
- metadata de fuentes equivalente en significado.

### Política de tolerancias

Las tolerancias numéricas deben:

1. definirse en el prompt antes de ejecutar la comparación;
2. justificarse por tipos y transformaciones;
3. no ampliarse después de observar diferencias para conseguir PASS;
4. quedar registradas en `R06` y `E06_RUNTIME.md`.

### Acciones manuales

- `M06-01`: ejecutar construcción Gold.
- `M06-02`: ejecutar SQL de validación/equivalencia.
- `M06-03`: registrar `DESCRIBE DETAIL/HISTORY` y conteos.
- `M06-04`: registrar comparación CSV ↔ Gold.
- `M06-05`: registrar comparación SQLite ↔ Gold.
- `M06-06`: documentar cualquier diferencia con tolerancia predefinida.
- `M06-07`: registrar evidencia en `E06_RUNTIME.md`.
- `M06-08`: autorizar commit/push/merge.

### Gate — Nivel 1 / MVP

Nivel 1 se alcanza cuando existe evidencia real de:

- Databricks;
- PySpark;
- Delta Lake;
- SQL;
- Bronze;
- Silver;
- Gold;
- cuatro fuentes;
- DQ;
- equivalencia con CSV y SQLite.

Desde ese punto el proyecto puede describirse como experiencia práctica de proyecto con:

`Databricks · PySpark · Delta Lake · SQL · Python`

No como experiencia profesional.

---

## 8.4 P07 — Lakehouse Hardening + Databricks SQL

**Dependencia:** P06 `GATE_PASSED`.  
**Branch sugerida:** `feat/lakehouse-hardening`.

### Objetivo único

Mejorar mantenibilidad, verificabilidad y consumo SQL después de que el MVP ya funcione.

### Alcance condicionado por evidencia

- extraer lógica realmente repetida;
- reducir duplicación observada;
- centralizar configuración estable cuando exista repetición suficiente;
- introducir tests útiles alrededor de contratos frágiles;
- consolidar funciones DQ cuando aporten valor;
- Databricks SQL / SQL Warehouse sobre Gold;
- queries analíticas/validación;
- estudiar `EXPLAIN`, physical plans, joins, shuffle y predicate pushdown en relación con el proyecto real.

No afirmar optimización sin problema medido, métrica y comparación.

### Acciones manuales

- `M07-01`: ejecutar queries definidas por el prompt.
- `M07-02`: ejecutar/conservar `EXPLAIN` o planes cuando correspondan.
- `M07-03`: ejecutar regresiones que requieran workspace.
- `M07-04`: registrar resultados en `E07_RUNTIME.md`.
- `M07-05`: entregar evidencia para cierre.

### Gate

La implementación queda más mantenible y consumible vía SQL sin alterar innecesariamente la semántica validada en P06.

---

## 8.5 P08 — Databricks Workflow

**Dependencia:** P07 `GATE_PASSED`.  
**Branch sugerida:** `feat/databricks-workflow`.

### Objetivo único

Orquestar de forma reproducible el pipeline funcional con la capacidad real disponible del workspace.

### DAG conceptual

```text
Bronze → Silver → Quality → Gold → Validation → Analytics
```

Este DAG expresa **responsabilidades y dependencias lógicas**. No obliga a crear seis tasks separadas.

La granularidad real de tasks debe justificarse por:

- dependencia real;
- aislamiento de fallo;
- utilidad del rerun;
- observabilidad;
- claridad operacional.

DQ o Validation pueden permanecer integradas en notebooks/SQL existentes si separarlas no resuelve un problema concreto.

### Acciones manuales

- `M08-01`: crear/verificar tasks y dependencias cuando la configuración requiera UI.
- `M08-02`: ejecutar el Workflow completo.
- `M08-03`: registrar run ID, estado de tasks y logs relevantes.
- `M08-04`: probar un rerun/control de recuperación cuando sea razonable.
- `M08-05`: registrar `E08_RUNTIME.md`.
- `M08-06`: autorizar cierre.

No se exige scheduling complejo.

### Gate — Nivel 2

El MVP puede ejecutarse mediante una orquestación reproducible y existe evidencia verificable de su ejecución.

---

## 8.6 P09 — Incremental Merge + Idempotency

**Dependencia:** P08 `GATE_PASSED`.  
**Branch sugerida:** `feat/incremental-merge`.

### Objetivo único

Demostrar un escenario incremental real sobre Delta usando `MERGE`, con no-change, update, insert y rerun lógico del mismo batch.

### Restricción de dominio

El experimento no puede violar silenciosamente:

- universo final de 32 comunas;
- grano de las tablas canónicas;
- contratos Gold/Silver ya validados.

No se crea una “comuna 33” solo para fabricar un insert.

El target debe ser:

- una entidad/grano donde el insert sea semánticamente válido; o
- una tabla experimental Delta claramente aislada del producto canónico.

La decisión exacta se toma al redactar P09 usando el estado real.

### Escenario mínimo

1. capturar estado inicial;
2. introducir batch sintético realista;
3. incluir registros sin cambios, al menos un update y al menos un insert semánticamente válido;
4. ejecutar `MERGE`;
5. verificar resultados;
6. ejecutar exactamente el mismo batch otra vez;
7. demostrar que el **estado lógico de datos** no cambia.

### Qué significa “mismo estado final”

Como mínimo:

- mismo set de keys;
- mismos valores de negocio;
- mismo row count;
- 0 duplicados no esperados;
- ausencia de cambios adicionales de contenido en el segundo rerun;
- checksum/hash lógico cuando aporte valor.

El transaction log puede registrar una nueva operación. Idempotencia lógica no significa “mismo `DESCRIBE HISTORY`”.

### Acciones manuales

- `M09-01`: crear/subir fixture incremental autorizado.
- `M09-02`: capturar estado inicial.
- `M09-03`: ejecutar primer `MERGE`.
- `M09-04`: verificar insert/update/no-change.
- `M09-05`: ejecutar el mismo batch por segunda vez.
- `M09-06`: comparar estado lógico y Delta history.
- `M09-07`: registrar `E09_RUNTIME.md`.

### Gate

Solo se declara idempotencia para el escenario probado cuando:

> **rerun del mismo batch → mismo estado lógico final**

---

## 8.7 P10 — Schema Change Experiment

**Dependencia:** P09 `GATE_PASSED`.  
**Branch sugerida:** `feat/schema-evolution`.

### Objetivo único

Demostrar una política deliberada de schema enforcement/evolution por capas sin degradar los productos canónicos ya validados.

### Aislamiento obligatorio

Los experimentos deben ejecutarse sobre:

- fixtures controlados;
- tablas experimentales;
- clone/restore u otro mecanismo de aislamiento explícitamente aprobado.

No dejar alteraciones irreversibles en Silver/Gold canónico solo para demostrar schema evolution.

El prompt debe definir:

```text
estado inicial
→ cambio compatible/incompatible
→ comportamiento esperado
→ evidencia
→ estado final
→ cleanup/restore
```

### Experimentos mínimos

1. cambio compatible/plausible;
2. cambio incompatible que deba fallar.

Preguntas:

- ¿qué acepta y registra Bronze?
- ¿qué exige Silver?
- ¿qué ignora/acepta/rechaza?
- ¿qué debe llegar a Gold?
- ¿qué prueba enforcement y no mera permisividad?

### Acciones manuales

- `M10-01`: crear/subir fixture compatible.
- `M10-02`: ejecutar y registrar comportamiento.
- `M10-03`: crear/subir fixture incompatible.
- `M10-04`: ejecutar y conservar la falla esperada.
- `M10-05`: confirmar ausencia de estado parcial incorrecto.
- `M10-06`: ejecutar cleanup/restore.
- `M10-07`: registrar `E10_RUNTIME.md`.

### Gate

La política frente a cambios de schema queda implementada, ejecutada, demostrada, documentada y el producto canónico queda en estado válido.

---

## 8.8 P11 — Power BI Serving

**Dependencia:** P10 `GATE_PASSED` y capacidad SQL utilizable.  
**Branch sugerida:** `feat/powerbi-serving` o branch documental equivalente.

### Objetivo único

Demostrar consumo analítico real:

```text
Gold → Databricks SQL / SQL Warehouse → Power BI
```

### Pre-flight obligatorio

Antes de diseñar la conexión:

- revisar documentación oficial vigente de Databricks;
- revisar documentación oficial vigente de Microsoft/Power BI;
- comprobar capacidades reales del workspace;
- comprobar autenticación disponible;
- determinar modo de conexión soportado;
- registrar limitaciones de edición/plan/cloud cuando correspondan.

No asumir que una capacidad observada meses antes sigue disponible.

### Acciones manuales imprescindibles

- `M11-01`: configurar autenticación/conexión en Power BI Desktop.
- `M11-02`: seleccionar Warehouse/endpoint.
- `M11-03`: documentar modo de conexión.
- `M11-04`: cargar productos Gold.
- `M11-05`: validar relaciones/tipos/KPIs mínimos.
- `M11-06`: contrastar valores contra queries Gold.
- `M11-07`: conservar evidencia sanitizada.
- `M11-08`: registrar `E11_RUNTIME.md`.

### Resultado posible

- `GATE_PASSED`: conexión y consumo demostrados.
- `CLOSED_WITH_LIMITATION`: el entorno impide una integración real y la limitación queda probada/documentada.
- `BLOCKED`: falta una dependencia o decisión todavía resoluble y no corresponde cerrar la etapa.

### Gate

Existe evidencia real de Power BI consumiendo Gold, o la etapa se cierra deliberadamente con una limitación verificable sin afirmar la capability como implementada.

---

## 8.9 P12 — Final Audit + Case Study

**Dependencia:** P11 `GATE_PASSED` o `CLOSED_WITH_LIMITATION`.  
**Branch sugerida:** `docs/final-audit-case-study`.

### Objetivo único

Auditar el proyecto completo sin agregar features por defecto y producir cierre técnico/publicable.

### Auditoría

Revisar:

- README y arquitectura;
- Local vs Lakehouse;
- Bronze/Silver/Gold;
- DQ/equivalencia;
- SQL/Databricks SQL;
- Workflow;
- `MERGE`;
- incrementalidad;
- idempotencia;
- schema enforcement/evolution;
- Power BI;
- claims públicos.

### Claims profesionales

Si se revisan CV o claims profesionales externos, `PERFIL_PROFESIONAL_MAESTRO_v1.3.1.md` debe incorporarse explícitamente como fuente aplicable.

Regla:

> experiencia práctica de proyecto Databricks ≠ experiencia profesional Databricks.

Si CV no forma parte del alcance de P12, limitar la revisión a README/portfolio/case study y tratar CV en una revisión separada.

### Estados técnicos finales

Cada capability se clasifica como:

- `IMPLEMENTED`;
- `VALIDATED`;
- `PARTIAL`;
- `PLANNED`;
- `NOT IMPLEMENTED`.

### Acciones manuales

- `M12-01`: verificar disponibilidad/reproducibilidad de evidencias externas.
- `M12-02`: decidir qué evidencia puede publicarse.
- `M12-03`: revisar claims públicos y, si está en scope, claims profesionales.
- `M12-04`: registrar evidencia/decisiones en `E12_RUNTIME.md`.
- `M12-05`: autorizar merge/publicación final.

### Case study

```text
Problema
→ Contexto
→ Solución
→ Arquitectura
→ Decisiones
→ Calidad
→ Modelo
→ Validación
→ Resultados
→ Limitaciones
→ Evidencia
```

### Gate — Nivel 3

Las capacidades avanzadas relevantes quedan clasificadas con evidencia y el proyecto puede explicarse mediante decisiones, implementación, trade-offs, resultados y limitaciones reales.

---

## 9. Matriz de intervención humana

| Etapa | Intervención humana principal | Intensidad |
|---|---|---|
| C04-D | Rerun Silver + SQL + evidencia | Media |
| P05 | Verificar/subir fuentes + Bronze/Silver + SQL | Alta |
| P06 | Gold + equivalencia CSV/SQLite | Media |
| P07 | SQL Warehouse / `EXPLAIN` / regresiones | Media |
| P08 | Workflow, ejecución y logs | Alta |
| P09 | Fixture incremental + dos `MERGE` | Alta |
| P10 | Fixtures schema + failure/cleanup | Alta |
| P11 | Power BI real | Muy alta / imprescindible |
| P12 | Evidencia, claims y publicación | Media |

Cada prompt debe incluir una sección `ACCIONES MANUALES REQUERIDAS` con IDs `Mxx-yy`, instrucción, resultado esperado y evidencia a conservar.

---

## 10. Matriz de trazabilidad mínima

| Elemento | Registro esperado |
|---|---|
| Objetivo | Prompt `Pxx/Cxx` |
| Estado inicial | branch, HEAD, `git status`, contratos |
| Implementación | diff + archivos |
| Verificación Codex | comandos/resultados en `Rxx` |
| Verificación externa | `Mxx-yy` + `Exx` |
| Criterios | CA-xx PASS/FAIL/NO EJECUTADA |
| Limitaciones | `Rxx` + `Exx` + revisión |
| Dictamen | APROBADO / CORREGIR / AUDITAR DE NUEVO / BLOQUEADO |
| Autoridad de avance | decisión humana |
| Resultado persistente | commit/PR/merge + tracker |

---

## 11. Política de actualización del tracker

Actualizar el tracker solo después de eventos verificables:

- prompt materializado;
- implementación completada;
- `Rxx` emitido;
- acción manual ejecutada;
- `Exx` actualizado;
- revisión emitida;
- commit/merge autorizado;
- bloqueo o cambio de alcance.

### 11.1 Registro mínimo de transición

Cada transición debe registrar:

- fecha;
- etapa;
- estado anterior → estado nuevo;
- evidencia;
- dictamen/revisión;
- decisión humana cuando corresponda.

### 11.2 Quién actualiza después de `Rxx`

Las transiciones posteriores al `Rxx` son administrativas de trazabilidad.

Pueden ser actualizadas:

- por Matías directamente; o
- mediante un prompt documental separado.

No se reabre un prompt de implementación solo para cambiar el estado del tracker.

### 11.3 Versionado

- cambios de estado/evidencia: registrar en changelog sin subir versión mayor/menor;
- cambios en orden, scope, gate, arquitectura o política operativa: nueva versión del tracker.

---

## 12. Riesgos activos

### R1 — replicar fragilidad de P04

Mitigación: C04-D antes de P05 y contrato de rerun explícito en P05.

### R2 — parser SINIM

A/B son SpreadsheetML/XML 2003 pese a `.xls`.

Mitigación: inspección del parser local y estrategia explícita de borde.

### R3 — P05 excesivamente amplio

Mitigación: checkpoints + condiciones objetivas de división.

### R4 — confundir snapshot rerun con idempotencia incremental

Mitigación: reservar `MERGE`/idempotencia para P09.

### R5 — tolerancias acomodadas retrospectivamente

Mitigación: definir tolerancias en P06 antes de ejecutar comparaciones.

### R6 — `MERGE` que viole el dominio

Mitigación: target/grano semánticamente válido o tabla experimental aislada.

### R7 — schema experiment sobre producto canónico

Mitigación: fixtures/targets aislados + cleanup/restore obligatorio.

### R8 — acciones externas sin evidencia persistente

Mitigación: `Exx` + referencias a evidencia primaria.

### R9 — capacidades externas cambian

Mitigación: pre-flight oficial/current en P11 y en toda etapa dependiente de plataforma cambiante.

### R10 — sobreingeniería

No incorporar Kafka, Airflow, dbt, Terraform, Kubernetes, streaming, MLflow, ADF u otras herramientas sin problema concreto.

---

## 13. Drift normativo conocido

### D-001 — nombre del repositorio

**Plan v1.0:** `mrav7/santiago-territorial-inequality-etl`  
**Estado vigente:** `mrav7/santiago-territorial-inequality`

Acción: actualizar en una futura versión del Plan Canónico; no reescribir v1.0 retroactivamente.

### D-002 — `AGENTS.md` / `CLAUDE.md`

**Plan v1.0:** ambos versionados e idénticos byte por byte.  
**Estado actual:** fueron retirados del repositorio público por una decisión posterior.

Acción pendiente: formalizar si estas instrucciones permanecen como artefactos locales/internos y reflejarlo en una futura actualización normativa.

No bloquea C04-D/P05.

### D-003 — estado P00–P04

**Plan v1.0:** roadmap inicial.  
**Estado vigente:** P00–P04 ya están cerrados con evidencia posterior.

Acción: este tracker registra el estado operativo sin modificar retrospectivamente el Plan v1.0.

---

## 14. Changelog del tracker

| Fecha | Versión | Etapa | Cambio | Evidencia |
|---|---:|---|---|---|
| 2026-09-25 | 1.0 | General | Creación del tracker operativo revisado | Estado remoto + Plan Canónico + metodología |
| 2026-09-25 | 1.0 | C04-D | Marcado `READY` como siguiente etapa | P04 cerrado + defectos/fragilidades documentados |

Agregar nuevas filas por cada transición relevante. No borrar entradas históricas para “limpiar” el relato.

---

## 15. Registro vivo de etapas

| Etapa | Estado operativo | Branch / HEAD | Prompt | Reporte | Evidencia runtime | Dictamen | Decisión humana | Próximo paso |
|---|---|---|---|---|---|---|---|---|
| C04-D | READY | por crear / `e9a8c4c...` base esperada | pendiente | pendiente | `E04-D_RUNTIME.md` pendiente | pendiente | pendiente | redactar/materializar C04-D |
| P05 | PLANNED | — | pendiente | pendiente | `E05_RUNTIME.md` pendiente | — | — | depende de C04-D |
| P06 | PLANNED | — | pendiente | pendiente | `E06_RUNTIME.md` pendiente | — | — | depende de P05 |
| P07 | PLANNED | — | pendiente | pendiente | `E07_RUNTIME.md` pendiente | — | — | depende de P06 |
| P08 | PLANNED | — | pendiente | pendiente | `E08_RUNTIME.md` pendiente | — | — | depende de P07 |
| P09 | PLANNED | — | pendiente | pendiente | `E09_RUNTIME.md` pendiente | — | — | depende de P08 |
| P10 | PLANNED | — | pendiente | pendiente | `E10_RUNTIME.md` pendiente | — | — | depende de P09 |
| P11 | PLANNED | — | pendiente | pendiente | `E11_RUNTIME.md` pendiente | — | — | depende de P10 |
| P12 | PLANNED | — | pendiente | pendiente | `E12_RUNTIME.md` pendiente | — | — | depende de P11 |

---

## 16. Criterio de avance

No iniciar una etapa posterior si el gate anterior presenta un fallo material no explicado.

Flujo:

```text
investigar
→ corregir o auditar
→ volver a validar
→ documentar
→ revisar
→ decisión humana
→ avanzar
```

No compensar una fase rota agregando una tecnología posterior.

---

## 17. Próximo paso

1. Adoptar este tracker en `docs/roadmap/lakehouse_execution_tracker.md`.
2. Verificar que `C04-D` no colisione con otro identificador interno.
3. Redactar el prompt canónico completo C04-D desde el HEAD real.
4. Materializar el prompt antes de ejecutar Codex.
5. Implementar el correctivo en branch focalizada.
6. Emitir `R04-D`.
7. Ejecutar las acciones `M04D-*` en Databricks.
8. Crear/actualizar `E04-D_RUNTIME.md`.
9. Revisar evidencia.
10. Solo con `C04-D = GATE_PASSED`, redactar P05.

---

## 18. Fuentes base del tracker

- `PLAN_CANONICO_SANTIAGO_ETL_DATABRICKS_v1.0.md`
- `REGLA_TRABAJO_CHATGPT_CODEX_PROMPTS_REPORTS.md`
- `README.md`
- `docs/architecture/lakehouse.md`
- estado remoto revisado de `mrav7/santiago-territorial-inequality`
- evidencia P00–P04 vigente al corte

Este tracker no reemplaza ninguna de esas fuentes; organiza la ejecución restante y su trazabilidad.
