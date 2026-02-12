# Focus Keeper - Anti-Procrastination App

**Focus Keeper** es una aplicación web de anti-procrastinación que utiliza la cámara de tu dispositivo para detectar cuando estás distraído y reproduce videos de atención para mantenerte enfocado. Este proyecto fue construido completamente usando **Tactical Agentic Coding (TAC)** - demostrando cómo los agentes de IA pueden desarrollar aplicaciones complejas de forma autónoma.

## ¿Qué es Focus Keeper?

Focus Keeper es una aplicación de seguimiento de atención basada en navegador que:

- **Detecta cuando estás distraído** usando machine learning para reconocimiento facial
- **Reproduce videos de atención** cuando detecta que has dejado de enfocarte
- **Procesa todo localmente** en tu navegador - sin transmisión de datos, privacidad primero
- **Rastrea estadísticas de sesión** incluyendo tiempo de enfoque, distracciones y puntaje de productividad
- **Funciona completamente en el cliente** - no requiere procesamiento ML en el backend

**Construido usando Tactical Agentic Coding**: Este proyecto demuestra TAC en acción - un paradigma de desarrollo donde los patrones de ingeniería se templetizan y los agentes de IA aprenden a operar el código base, escalando el impacto a través del cómputo en lugar de programación directa.

## Tecnologías Utilizadas

- **Frontend**: Vanilla JavaScript, TensorFlow.js, MediaPipe Face Mesh
- **Backend**: Python, FastAPI, Uvicorn
- **IA/ML**: Claude Sonnet (via Anthropic API), TensorFlow.js para detección facial
- **Deployment**: Vercel serverless functions
- **Testing**: Pytest (Python), Jest (JavaScript)
- **CI/CD**: GitHub webhooks, automated workflows
- **Tools**: uv (Python package management), gh CLI (GitHub operations)

## Características de Focus Keeper

### Características Principales

- **Detección facial en tiempo real**: Utiliza TensorFlow.js con MediaPipe Face Mesh para detectar tu rostro y rastrear tu mirada
- **Monitoreo de distracciones**: Detecta automáticamente cuando miras lejos de la pantalla o abandonas tu asiento
- **Intervenciones de atención**: Reproduce videos atractivos cuando se detecta distracción para captar tu atención
- **Estadísticas de sesión**: Rastrea tiempo de enfoque, distracciones y productividad general
- **Diseño que prioriza la privacidad**: Todo el procesamiento ocurre localmente en tu navegador - ningún video se almacena o transmite
- **No requiere backend**: Se ejecuta completamente del lado del cliente sin procesamiento ML en el servidor

### Compatibilidad de Navegadores

Funciona mejor en navegadores modernos con soporte WebRTC y WebGL:

- **Chrome** (recomendado) - v90+
- **Firefox** - v88+
- **Safari** - v14+
- **Edge** - v90+

**Requisitos**: Permisos de acceso a la cámara, JavaScript habilitado, soporte WebGL

Para más detalles sobre Focus Keeper, consulta el [README del Frontend](apps/frontend/README.md).

## Estructura del Proyecto

```
tac-challenge/
├── .claude/              # Configuración y comandos de Claude
├── adws/                 # AI Developer Workflows - workflows de IA para automatización
│   ├── adw_modules/      # Módulos core (agent, github, etc.)
│   └── adw_*.py          # Scripts de workflows
├── apps/                 # Capa de aplicación - código de la aplicación
│   ├── adw_server/       # Servidor de automatización ADW
│   │   ├── core/         # Módulos core (config, handlers, integration)
│   │   ├── server.py     # Aplicación FastAPI
│   │   └── main.py       # Punto de entrada
│   └── frontend/         # Focus Keeper - aplicación anti-procrastinación
│       ├── index.html    # Aplicación web principal
│       ├── app.js        # Lógica de la aplicación
│       ├── face-detection.js  # Detección facial y rastreo de mirada
│       ├── video-player.js    # Manejo de videos de intervención
│       └── test/         # Tests del frontend (Jest)
├── api/                  # Vercel deployment - funciones serverless
├── docs/                 # Documentación adicional
│   └── TESTING.md        # Guía completa de testing
├── specs/                # Especificaciones de implementación - planes para agentes
├── scripts/              # Scripts de inicio y utilidades
├── tests/                # Tests del backend Python (Pytest)
├── .env.example          # Template de configuración
├── requirements.txt      # Dependencias Python
├── vercel.json           # Configuración de deployment Vercel
└── VERCEL_DEPLOYMENT.md  # Guía de deployment
```

## Quick Start - Ejecutar la Aplicación

### 1. Configurar entorno

```bash
# Copiar template de configuración
cp apps/adw_server/.env.example .env

# Editar .env y configurar:
# - GITHUB_WEBHOOK_SECRET (para webhooks de GitHub)
# - ANTHROPIC_API_KEY (para workflows ADW)
```

### 2. Iniciar el Servidor

El servidor FastAPI sirve tanto la aplicación Focus Keeper como el sistema de automatización ADW:

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

### 3. Acceder a Focus Keeper

Una vez que el servidor esté ejecutándose:

1. Abre tu navegador y navega a: **http://localhost:8000/app**
2. El navegador solicitará permisos de cámara - haz clic en "Allow"
3. Haz clic en "Start Session" para comenzar a rastrear tu enfoque
4. ¡Ponte a trabajar! La app monitoreará tu atención y te alertará si te distraes

### 4. Endpoints Disponibles

- **Focus Keeper app**: http://localhost:8000/app - La aplicación principal
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

**Labels soportados:**
- `implement` / `bug` → Workflow completo (plan + implementación)
- `feature` → Solo planning
- `chore` / `plan` → Solo planning

**Pull Request Review Workflow:**

Cuando se crea o actualiza un Pull Request que referencia un issue (con "Closes #N", "Fixes #N", o "Resolves #N"), se ejecuta automáticamente un workflow de revisión que:
- Analiza el código usando Claude
- Ejecuta los tests del proyecto
- Captura screenshots si hay cambios en UI (futuro)
- Determina el estado de aprobación basado en el análisis
- Publica los resultados en el thread del issue

**Estados de Revisión:**

El workflow de revisión puede resultar en tres estados:
- **APPROVED**: El código cumple con los estándares, tests pasan, sin problemas detectados
- **CHANGES REQUESTED**: Se encontraron problemas que requieren correcciones
- **NEEDS DISCUSSION**: Requiere revisión manual o discusión (casos ambiguos)

**Acciones Automáticas Post-Revisión:**

El sistema puede realizar acciones automáticas basadas en el resultado de la revisión:

- **APPROVED**:
  - **Auto-merge** del PR (configurable con `AUTO_MERGE_ON_APPROVAL=true`)
  - El PR se fusiona automáticamente a la rama base
  - Método de merge configurable (squash, merge, rebase)

- **CHANGES REQUESTED**:
  - **Auto-reimplement** con feedback de revisión (configurable con `AUTO_REIMPLEMENT_ON_CHANGES=true`)
  - El agente lee el feedback de la revisión
  - Implementa automáticamente las correcciones solicitadas
  - Crea un nuevo commit con los cambios
  - El PR actualizado dispara una nueva revisión automática

- **NEEDS DISCUSSION**:
  - Solo publica resultados
  - Requiere intervención manual del desarrollador

**Configuración de Acciones Post-Revisión:**

Las acciones automáticas pueden configurarse en `.env`:
```bash
AUTO_MERGE_ON_APPROVAL=true          # Merge automático en aprobación
AUTO_REIMPLEMENT_ON_CHANGES=true     # Re-implementación automática en cambios solicitados
MERGE_METHOD=squash                  # Método de merge (squash, merge, rebase)
MAX_REIMPLEMENT_ATTEMPTS=3           # Máximo de intentos para prevenir loops
```

**Protección contra Loops Infinitos:**

El sistema implementa protección robusta contra loops de re-implementación:
- **Rastrea intentos por issue**: Cuenta cuántas veces se ha intentado re-implementar
- **Límite configurable**: Después de alcanzar `MAX_REIMPLEMENT_ATTEMPTS` (default: 3), detiene la auto-reimplementación
- **Requiere intervención manual**: Después del límite, los cambios deben hacerse manualmente
- **Reset en merge exitoso**: El contador se reinicia cuando un PR se fusiona exitosamente
- **Previene escenarios de falla repetida**: Evita que el agente genere código que falla la revisión indefinidamente

Para más detalles sobre el workflow de revisión y automatización post-revisión, consulta el [README del ADW Server](apps/adw_server/README.md).

## Testing

El proyecto incluye infraestructura de testing comprehensiva para ambos backend Python y frontend JavaScript, asegurando calidad y confiabilidad del código.

### Estructura de Tests

- **Tests de Python** (`tests/`): Tests del backend usando Pytest
  - Tests de configuración
  - Tests de handlers de eventos
  - Tests de integración de GitHub
  - Tests de workflows ADW

- **Tests de Frontend** (`apps/frontend/test/`): Tests de JavaScript usando Jest
  - Tests de detección facial
  - Tests de monitoreo de distracción
  - Tests de reproducción de videos
  - Tests de gestión de sesión

- **Script Unificado**: `scripts/run_tests.sh` - Ejecuta todos los tests con una sola línea de comando

### Ejecutar Tests

**Todos los tests:**

```bash
./scripts/run_tests.sh
```

**Solo tests de Python:**

```bash
./scripts/run_tests.sh --python-only
# O directamente:
uv run pytest tests/ -v
```

**Solo tests de frontend:**

```bash
./scripts/run_tests.sh --frontend-only
# O directamente:
cd apps/frontend && npm test
```

**Con coverage:**

```bash
./scripts/run_tests.sh --coverage
```

### Objetivos de Coverage

- **Backend Python**: >80% coverage
- **Frontend JavaScript**: >75% coverage

Para ver reportes de coverage:
```bash
# Python coverage report
uv run pytest tests/ --cov=apps --cov=adws --cov-report=html
open htmlcov/index.html

# Frontend coverage report
cd apps/frontend && npm test -- --coverage
```

Para guía completa de testing, consulta la [Guía de Testing](docs/TESTING.md).

## Deployment

El proyecto incluye soporte completo para deployment en producción usando Vercel.

### Vercel Deployment

El proyecto está configurado para deployment serverless en Vercel:

- **FastAPI app serverless**: El ADW server se ejecuta como función serverless
- **Frontend estático**: Focus Keeper se sirve como archivos estáticos
- **Configuración automática**: `vercel.json` configura rutas y rewrites
- **Variables de entorno**: Configurables en el dashboard de Vercel

### Quick Deploy

```bash
# Ver VERCEL_DEPLOYMENT.md para instrucciones detalladas
vercel deploy
```

### Configuración Requerida

Variables de entorno en Vercel dashboard:

```bash
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
AUTO_MERGE_ON_APPROVAL=true                    # Opcional
AUTO_REIMPLEMENT_ON_CHANGES=true              # Opcional
MERGE_METHOD=squash                           # Opcional
MAX_REIMPLEMENT_ATTEMPTS=3                    # Opcional
```

### Consideraciones de Deployment

- **Límites de funciones serverless**: Vercel tiene timeouts de ejecución (10s hobby, 60s pro)
- **Filesystem efímero**: Solo `/tmp` es escribible, archivos se borran entre invocaciones
- **Cold starts**: Primera ejecución puede ser más lenta
- **Escalamiento automático**: Vercel maneja el escalamiento automáticamente

Para guía completa de deployment, consulta la [Guía de Deployment Vercel](VERCEL_DEPLOYMENT.md).

## Desarrollo

### Environment Setup

El proyecto utiliza infraestructura de testing comprehensiva para ambos backend y frontend, asegurando calidad del código en todos los componentes.

### Hot Reload

- **Backend FastAPI**: Auto-reload habilitado en modo desarrollo (uvicorn con `--reload`)
- **Frontend**: Servido como archivos estáticos, recarga automática en cambios (usa live server o similar)

### Scripts Disponibles

```bash
# Los scripts de inicio y utilidades están en scripts/
ls scripts/

# Ejemplos:
./scripts/start_webhook_server.sh     # Inicia el servidor
./scripts/run_tests.sh                # Ejecuta todos los tests
```

### Estructura de Directorios

- **`adws/`**: Workflows de IA para desarrollo - scripts de automatización
- **`apps/frontend/`**: Focus Keeper app - aplicación anti-procrastinación
- **`apps/adw_server/`**: Servidor de automatización ADW
- **`specs/`**: Especificaciones de implementación - planes para agentes
- **`scripts/`**: Scripts de utilidad y inicio
- **`tests/`**: Tests del backend Python
- **`docs/`**: Documentación adicional

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

## Troubleshooting

### Problemas con Focus Keeper

#### Cámara no funciona

**Problema**: Error "Failed to access camera"

**Soluciones**:
- Verifica permisos del navegador (Settings → Privacy → Camera)
- Asegura que ninguna otra app esté usando la cámara
- Prueba con otro navegador
- En macOS: System Preferences → Security & Privacy → Camera

#### Rostro no detectado

**Problema**: Estado muestra "Distracted" incluso cuando estás presente

**Soluciones**:
- Mejora la iluminación (agrega lámpara de escritorio, abre cortinas)
- Quita gafas si causan reflejos
- Acércate más a la cámara
- Asegura que tu rostro esté centrado en el frame

#### Modelo no carga

**Problema**: Error "Failed to load face detection model"

**Soluciones**:
- Verifica conexión a internet (TensorFlow.js carga desde CDN)
- Limpia cache del navegador y recarga
- Deshabilita ad blockers que puedan bloquear requests CDN
- Prueba con otro navegador

#### Rendimiento pobre / lag

**Problema**: App lenta o no responde

**Soluciones**:
- Cierra otras tabs del navegador
- Usa Chrome (mejor rendimiento WebGL)
- Cierra otras aplicaciones que usen GPU
- Verifica que tu dispositivo tenga recursos suficientes

### Problemas con ADW Automation

#### Webhook signature validation falla

**Problema**: Webhooks rechazados con error de validación

**Soluciones**:
- Verifica que `GITHUB_WEBHOOK_SECRET` en `.env` coincida con GitHub settings
- Asegura que el secret no tenga espacios o caracteres especiales
- Regenera el secret si es necesario

#### Workflows ADW no se disparan

**Problema**: Issues con labels no activan workflows

**Soluciones**:
- Verifica que el issue tenga el label correcto (`implement`, `bug`, `feature`, `chore`)
- Revisa logs del servidor para errores
- Asegura que webhooks estén configurados correctamente en GitHub
- Verifica que `ANTHROPIC_API_KEY` esté configurada

#### Auto-merge falla

**Problema**: PR aprobado pero no se fusiona automáticamente

**Soluciones**:
- Verifica que `AUTO_MERGE_ON_APPROVAL=true` en `.env`
- Asegura que no haya conflictos de merge
- Verifica permisos del token de GitHub (debe poder mergear)
- Revisa protecciones de rama en GitHub settings

#### Loops de re-implementación

**Problema**: El agente intenta re-implementar indefinidamente

**Soluciones**:
- Verifica `MAX_REIMPLEMENT_ATTEMPTS` en `.env` (default: 3)
- Proporciona feedback más claro en las revisiones
- Considera aumentar el límite si los cambios son complejos
- Revisa el contador de intentos en los logs

Para troubleshooting más detallado, consulta los READMEs de cada componente:
- [Frontend Troubleshooting](apps/frontend/README.md#troubleshooting)
- [ADW Server README](apps/adw_server/README.md)

## Documentación Adicional

### Documentación de Usuario

- **[Focus Keeper App](apps/frontend/README.md)** - Documentación completa de la aplicación anti-procrastinación
  - Características y funcionalidad
  - Guía de uso
  - Configuración
  - Troubleshooting

### Documentación de Desarrollo

- **[ADW README](adws/README.md)** - Documentación de AI Developer Workflows
  - Soporte SDK
  - Patrones de workflow
  - Observabilidad

- **[ADW Server README](apps/adw_server/README.md)** - Servidor de automatización
  - PR review workflow
  - Auto-merge y auto-reimplement
  - Loop protection
  - Configuración

- **[Testing Guide](docs/TESTING.md)** - Guía completa de testing
  - Tests de Python
  - Tests de frontend
  - Coverage goals
  - Best practices

- **[Deployment Guide](VERCEL_DEPLOYMENT.md)** - Guía de deployment Vercel
  - Configuración serverless
  - Variables de entorno
  - Consideraciones de producción

- **Especificaciones** (`specs/`) - Planes de implementación y especificaciones de features

## Licencia

Este proyecto es un desafío educativo para demostrar Tactical Agentic Coding.
