# Docker Multi-Service Deployment Guide

Dit document beschrijft de Docker configuratie met aparte services voor frontend en backend.

## 📁 Bestanden Overzicht

| Bestand | Beschrijving |
|---------|--------------|
| `Dockerfile.frontend` | Frontend build (Vite + Nginx) |
| `Dockerfile.backend` | Backend build (Python + Bun server) |
| `nginx.conf` | Nginx configuratie voor frontend |
| `docker-compose.yml` | Development configuratie |
| `docker-compose.production.yml` | Productie configuratie met Traefik |

---

## 🔧 Environment Variabelen

### Backend (Runtime)

Deze variabelen worden **tijdens runtime** ingelezen door de backend container:

| Variabele | Verplicht | Standaard | Beschrijving |
|-----------|-----------|-----------|--------------|
| `ANTHROPIC_API_KEY` | ⚠️ Aanbevolen | - | Claude AI API key |
| `SERVER_PORT` | Nee | `4000` | Backend server poort |
| `NODE_ENV` | Nee | `production` | Node environment |
| `DASHBOARD_URL` | Nee | `https://agents.bimai.nl` | URL voor callbacks |
| `DOMAIN` | Nee | `agents.bimai.nl` | Domein voor Traefik |

### Frontend (Build-time)

⚠️ **BELANGRIJK**: Deze variabelen worden **tijdens de Docker build** ingebakken in de statische bestanden!

| Variabele | Verplicht | Productie Waarde | Beschrijving |
|-----------|-----------|------------------|--------------|
| `VITE_API_URL` | Nee | `""` (leeg) | API URL, leeg = relatieve URLs |
| `VITE_WS_URL` | Nee | `""` (leeg) | WebSocket URL, leeg = auto-detect |
| `VITE_API_PORT` | Nee | `4000` | API poort |
| `VITE_MAX_EVENTS` | Nee | `300` | Max events in dashboard |

---

## 🚀 Productie Server Setup

### Stap 1: Maak een `.env` bestand

```bash
# Op je productie server
cd /pad/naar/project
cp .env.example .env
nano .env
```

### Stap 2: Vul de vereiste variabelen in

```env
# VERPLICHT voor productie:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# OPTIONEEL (hebben goede standaardwaarden):
DOMAIN=agents.bimai.nl
DASHBOARD_URL=https://agents.bimai.nl
SERVER_PORT=4000
NODE_ENV=production

# Frontend build-time (laat leeg voor productie!)
VITE_API_URL=
VITE_WS_URL=
VITE_MAX_EVENTS=300
```

### Stap 3: Start de services

```bash
# Voor productie met Traefik/Dokploy:
docker compose -f docker-compose.production.yml up -d --build

# Of voor development:
docker compose up -d --build
```

---

## 📋 Minimale Productie Configuratie

Als je snel wilt deployen, zijn dit de **enige** variabelen die je MOET instellen:

```env
# .env op productie server
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

Alle andere variabelen hebben goede standaardwaarden!

---

## 🔄 Architectuur

```
┌─────────────────────────────────────────────────────────────┐
│                         Traefik                             │
│                    (Reverse Proxy + SSL)                    │
└─────────────────┬───────────────────────────┬───────────────┘
                  │                           │
                  │ /api, /events, /stream    │ / (alle andere routes)
                  │ (priority: 10)            │ (priority: 1)
                  ▼                           ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│         Backend             │   │         Frontend            │
│    (Dockerfile.backend)     │   │    (Dockerfile.frontend)    │
│                             │   │                             │
│  • Python Orchestrator      │   │  • Nginx                    │
│  • Bun API Server (:4000)   │   │  • Vue.js App (:80)         │
│  • Claude SDK               │   │  • Static Files             │
│  • WebSocket Server         │   │                             │
└─────────────────────────────┘   └─────────────────────────────┘
         │                                    │
         │                                    │
         ▼                                    │
┌─────────────────────────────┐               │
│      Volumes                │◄──────────────┘
│  • uploads_data             │   (frontend maakt API calls
│  • logs_data                │    naar backend via Traefik)
│  • workspace_data           │
└─────────────────────────────┘
```

---

## 🐳 Docker Commands

```bash
# Build beide services
docker compose -f docker-compose.production.yml build

# Start services
docker compose -f docker-compose.production.yml up -d

# Bekijk logs
docker compose -f docker-compose.production.yml logs -f

# Bekijk logs van specifieke service
docker compose -f docker-compose.production.yml logs -f backend
docker compose -f docker-compose.production.yml logs -f frontend

# Restart services
docker compose -f docker-compose.production.yml restart

# Stop services
docker compose -f docker-compose.production.yml down

# Rebuild en restart
docker compose -f docker-compose.production.yml up -d --build --force-recreate
```

---

## ⚠️ Belangrijk: Frontend Build-time Variabelen

De frontend variabelen (`VITE_*`) worden **tijdens de build** ingebakken in de JavaScript bestanden. Dit betekent:

1. **Na het wijzigen van VITE_* variabelen moet je opnieuw builden**
2. Je kunt ze niet wijzigen zonder een nieuwe Docker build
3. Voor productie: laat `VITE_API_URL` en `VITE_WS_URL` **leeg** - de frontend detecteert automatisch de correcte URLs

```bash
# Na wijziging van VITE_* variabelen:
docker compose -f docker-compose.production.yml build frontend
docker compose -f docker-compose.production.yml up -d frontend
```

---

## 🔍 Troubleshooting

### Frontend kan backend niet bereiken
- Controleer of beide containers in hetzelfde netwerk zitten
- Controleer Traefik labels en routing rules
- Bekijk nginx logs: `docker compose logs frontend`

### WebSocket connectie faalt
- Controleer of de WebSocket middleware in Traefik correct is geconfigureerd
- Test met: `wscat -c wss://agents.bimai.nl/stream`

### API Key werkt niet
- Controleer of `ANTHROPIC_API_KEY` correct is ingesteld
- Bekijk backend logs: `docker compose logs backend`
