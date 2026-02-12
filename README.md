# TAC Challenge - Tactical Agentic Coding

Este proyecto demuestra **Tactical Agentic Coding (TAC)** - un paradigma de desarrollo donde los patrones de ingeniería se templetizan y los agentes de IA aprenden a operar el código base, escalando el impacto a través del cómputo en lugar de programación directa.

## Estructura del Proyecto

```
tac-challenge/
├── .claude/              # Configuración y comandos de Claude
├── adws/                 # AI Developer Workflows
│   ├── adw_modules/      # Módulos core (agent, github, etc.)
│   └── adw_*.py          # Scripts de workflows
├── apps/                 # Capa de aplicación
│   └── adw_server/       # Servidor de automatización ADW
│       ├── core/         # Módulos core (config, handlers, integration)
│       ├── server.py     # Aplicación FastAPI
│       └── main.py       # Punto de entrada
├── specs/                # Especificaciones de implementación
├── scripts/              # Scripts de inicio
├── tests/                # Tests del proyecto
├── .env.example          # Template de configuración
└── requirements.txt      # Dependencias Python
```

## Quick Start

### 1. Configurar entorno

```bash
# Copiar template de configuración
cp apps/adw_server/.env.example .env

# Editar .env y configurar:
# - GITHUB_WEBHOOK_SECRET
# - ANTHROPIC_API_KEY
```

### 2. Iniciar ADW Server

El ADW Server es una herramienta de automatización que:
- Recibe webhooks de GitHub
- Dispara workflows de ADW automáticamente
- Provee endpoints de salud y monitoreo

```bash
# Desde el root del proyecto
./scripts/start_webhook_server.sh
```

**Métodos alternativos:**

<details>
<summary>Usando uv (recomendado - maneja dependencias automáticamente)</summary>

```bash
PYTHONPATH=. uv run \
  --with fastapi \
  --with "uvicorn[standard]" \
  --with pydantic \
  --with pydantic-settings \
  --with python-dotenv \
  uvicorn apps.adw_server.server:app --host 0.0.0.0 --port 8000
```
</details>

<details>
<summary>Usando Python directamente</summary>

```bash
pip install -r requirements.txt
python apps/adw_server/main.py
```
</details>

### 3. Endpoints

- **Health check**: http://localhost:8000/health
- **Readiness check**: http://localhost:8000/health/ready
- **GitHub webhooks**: http://localhost:8000/ (POST)

## Tactical Agentic Coding (TAC)

### ¿Qué es TAC?

TAC es un paradigma donde:
- Los patrones de ingeniería se templetizan
- Los agentes de IA aprenden a operar el código base
- Se escala el impacto a través del cómputo, no del esfuerzo directo

### Capas del Proyecto

#### Capa Agentica

Responsable de la codificación agentica - donde se templetizan los patrones de ingeniería:

- **`.claude/commands/`**: Templates de comandos reutilizables
- **`adws/`**: AI Developer Workflows ejecutables
- **`specs/`**: Especificaciones que guían las acciones de los agentes

#### Capa de Aplicación

El código de tu aplicación real - sobre lo que operan los agentes:

- **`apps/`**: Código de aplicación
  - `adw_server/`: Herramienta de automatización ADW (NO es el servidor principal de la app)

## ADW Server

El ADW Server es una **herramienta de automatización**, no el servidor principal de la aplicación.

**Propósito:**
- Integración GitHub → ADW workflows
- Automatización de tareas de desarrollo
- Monitoreo de salud

**Configuración de GitHub Webhook:**

1. Ir a Settings → Webhooks → Add webhook
2. Payload URL: `https://tu-servidor.com/`
3. Content type: `application/json`
4. Secret: (mismo que `GITHUB_WEBHOOK_SECRET` en `.env`)
5. Events: Seleccionar "Issues" y "Pull requests"

### Deployment a Vercel

El proyecto incluye configuración para deployment serverless en Vercel:

**Pre-requisitos:**
- Cuenta de Vercel
- GitHub repository conectado a Vercel

**Pasos de deployment:**

1. **Conectar repository a Vercel:**
   - Ir a [Vercel Dashboard](https://vercel.com/dashboard)
   - Click en "Import Project"
   - Seleccionar tu GitHub repository
   - Vercel detectará automáticamente la configuración de `vercel.json`

2. **Configurar variables de entorno en Vercel:**

   Ir a Project Settings → Environment Variables y agregar:

   - `GITHUB_WEBHOOK_SECRET`: Tu secret de webhook (generar con: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - `ANTHROPIC_API_KEY`: Tu API key de Anthropic (obtener de https://console.anthropic.com/)
   - `ENVIRONMENT`: `production`
   - `LOG_LEVEL`: `INFO` (o `WARNING` para producción)
   - `ADW_DEFAULT_MODEL`: `sonnet`
   - `CORS_ENABLED`: `true`

3. **Deploy:**
   - Click en "Deploy"
   - Vercel construirá y desplegará automáticamente
   - Obtendrás una URL de deployment (ej: `https://tu-proyecto.vercel.app`)

4. **Configurar GitHub Webhook con URL de Vercel:**
   - Usar la URL de Vercel como Payload URL: `https://tu-proyecto.vercel.app/`
   - Configurar el mismo secret que configuraste en Vercel

**Limitaciones en Vercel:**

- **Serverless environment**: Las funciones tienen tiempo de ejecución limitado (10 segundos en plan gratuito, 60 segundos en Pro)
- **Stateless**: No hay persistencia de archivos entre invocaciones
- **Working directory**: Los workflows ADW pueden tener limitaciones en el ambiente serverless
- **Static files**: La app frontend se sirve desde el CDN de Vercel

**Nota**: Para workflows ADW complejos que requieren ejecutar git, crear archivos, o tareas de larga duración, considera usar un deployment tradicional en servidor VPS o contenedor Docker en lugar de serverless.

**Labels soportados:**
- `implement` / `bug` → Workflow completo (plan + implementación)
- `feature` → Solo planning
- `chore` / `plan` → Solo planning

**Pull Request Review Workflow:**

Cuando se crea o actualiza un Pull Request que referencia un issue (con "Closes #N", "Fixes #N", o "Resolves #N"), se ejecuta automáticamente un workflow de revisión que:
- Analiza el código usando Claude
- Ejecuta los tests del proyecto
- Captura screenshots si hay cambios en UI (futuro)
- Publica los resultados en el thread del issue

Los PRs deben incluir referencias a issues en la descripción para activar el workflow de revisión automática.

## Desarrollo

### Testing

El proyecto incluye tests comprehensivos para el backend Python y el frontend JavaScript.

**Ejecutar todos los tests:**

```bash
./scripts/run_tests.sh
```

**Ejecutar solo tests de Python:**

```bash
./scripts/run_tests.sh --python-only
# O directamente:
uv run pytest tests/ -v
```

**Ejecutar solo tests de frontend:**

```bash
./scripts/run_tests.sh --frontend-only
# O directamente:
cd apps/frontend && npm test
```

**Ejecutar tests con coverage:**

```bash
./scripts/run_tests.sh --coverage
```

Para más detalles sobre testing, consulta la [Guía de Testing](docs/TESTING.md).

### Scripts

```bash
# Los scripts de inicio están en scripts/
ls scripts/
```

### Estructura de Directorios

- **`adws/`**: Workflows de IA para desarrollo
- **`apps/`**: Código de aplicación
- **`specs/`**: Especificaciones de implementación
- **`scripts/`**: Scripts de utilidad
- **`tests/`**: Tests del proyecto

## 12 Puntos de Apalancamiento del Agentic Coding

### En el Agente (Core Four)

1. Context
2. Model
3. Prompt
4. Tools

### A través del Agente

5. Standard Output
6. Types
7. Docs
8. Tests
9. Architecture
10. Plans
11. Templates
12. AI Developer Workflows

## Flexibilidad

Esta es *una forma* de organizar la capa agentica. El principio clave es crear un entorno estructurado donde:
- Los patrones de ingeniería sean templates reutilizables
- Los agentes tengan instrucciones claras de cómo operar el código base
- Los workflows sean componibles y escalables
- La salida sea observable y debuggeable

Siéntete libre de adaptar esta estructura a tus necesidades específicas.

## Documentación Adicional

- **ADW README**: `adws/README.md` - Documentación completa de AI Developer Workflows
- **ADW Server README**: `apps/adw_server/README.md` - Documentación del servidor de automatización
- **Testing Guide**: `docs/TESTING.md` - Guía completa de testing
- **Especificaciones**: `specs/` - Planes de implementación

## Licencia

Este proyecto es un desafío educativo para demostrar Tactical Agentic Coding.
