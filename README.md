# SupportDesk — Support Ticket System

A full-stack support ticket management application with AI-powered triage, built with Django, React, PostgreSQL, and Docker.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [LLM Integration](#llm-integration)
- [Design Decisions](#design-decisions)
- [Environment Variables](#environment-variables)

---

## Tech Stack

| Layer       | Technology                             |
|-------------|----------------------------------------|
| Backend     | Django 4.2 + Django REST Framework    |
| Database    | PostgreSQL 15                          |
| Frontend    | React 18 + Vite                        |
| LLM         | Groq (llama-3.1-8b-instant) — **free tier**       |
| Container   | Docker + Docker Compose                |

---

## Features

- **Submit tickets** with title, description, category, and priority
- **AI auto-classification** — as you type a description, Claude suggests the category and priority in real-time
- **Override suggestions** — dropdowns are pre-filled by the AI but fully editable
- **Filter & search** — filter tickets by category, priority, and status; full-text search across title and description
- **Status management** — click any ticket to change its status inline
- **Stats dashboard** — live metrics with priority and category breakdowns using DB-level aggregation
- **Graceful degradation** — ticket submission always works even if the LLM API is unavailable

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Docker Compose)
- An Anthropic API key (optional — the app works without it, just without AI suggestions)

### 1. Clone / unzip the project

```bash
unzip support-ticket-system.zip
cd support-ticket-system
```

### 2. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key (free at [console.groq.com](https://console.groq.com) — no credit card required):

```env
GROQ_API_KEY=gsk_your_actual_key_here
```

> **No key?** That's fine. Leave the value empty — the app still works, it just falls back to `general / medium` as the default classification.

### 3. Start everything

```bash
docker-compose up --build
```

Docker will:
1. Start a PostgreSQL 15 container
2. Build and start the Django backend (auto-runs migrations)
3. Build and start the React frontend (Vite dev server)

### 4. Open the app

| Service   | URL                      |
|-----------|--------------------------|
| Frontend  | http://localhost:5173    |
| Backend API | http://localhost:8000/api/ |

---

## Project Structure

```
support-ticket-system/
├── backend/
│   ├── config/
│   │   ├── settings.py         # Django settings (env-driven)
│   │   ├── urls.py             # Root URL routing
│   │   └── wsgi.py
│   ├── tickets/
│   │   ├── models.py           # Ticket model with DB-level constraints
│   │   ├── serializers.py      # DRF serializers + input validation
│   │   ├── views.py            # API views (list, detail, stats, classify)
│   │   ├── urls.py             # tickets/* URL patterns
│   │   └── llm.py              # Anthropic integration + prompt
│   ├── entrypoint.sh           # Waits for DB, migrates, starts gunicorn
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── tickets.js      # Axios API client
│   │   ├── components/
│   │   │   ├── TicketForm.jsx  # New ticket form + AI suggestion UX
│   │   │   ├── TicketList.jsx  # Paginated list with filter state
│   │   │   ├── TicketCard.jsx  # Individual ticket + inline status update
│   │   │   ├── FilterBar.jsx   # Search + filter controls
│   │   │   └── StatsDashboard.jsx # Metrics + breakdown charts
│   │   ├── App.jsx             # Root component, tab navigation
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Design system (CSS variables + utility classes)
│   ├── index.html
│   ├── vite.config.js          # Vite dev server + API proxy
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## API Reference

### `POST /api/tickets/`
Create a new ticket.

**Body:**
```json
{
  "title": "Cannot log in to my account",
  "description": "I keep getting a 403 error when I try to sign in...",
  "category": "account",
  "priority": "high"
}
```
**Returns:** `201 Created` with the ticket object.

---

### `GET /api/tickets/`
List all tickets, newest first.

**Query params:**
| Param | Description |
|-------|-------------|
| `category` | Filter by: `billing`, `technical`, `account`, `general` |
| `priority` | Filter by: `low`, `medium`, `high`, `critical` |
| `status` | Filter by: `open`, `in_progress`, `resolved`, `closed` |
| `search` | Full-text search across `title` and `description` |

All filters can be combined.

---

### `PATCH /api/tickets/<id>/`
Partial update — change status, category, priority, etc.

**Body:** Any subset of ticket fields.

---

### `GET /api/tickets/stats/`
Aggregated statistics.

**Response:**
```json
{
  "total_tickets": 124,
  "open_tickets": 67,
  "avg_tickets_per_day": 8.3,
  "priority_breakdown": { "low": 30, "medium": 52, "high": 31, "critical": 11 },
  "category_breakdown": { "billing": 28, "technical": 55, "account": 22, "general": 19 }
}
```

> All aggregation happens at the database level using Django ORM `Count`, `annotate`, and `TruncDate` — no Python loops over querysets.

---

### `POST /api/tickets/classify/`
Send a description, get AI-suggested category and priority.

**Body:**
```json
{ "description": "I was charged twice for my subscription this month." }
```

**Response:**
```json
{ "suggested_category": "billing", "suggested_priority": "high" }
```

**On LLM failure:** Returns `{ "suggested_category": "general", "suggested_priority": "medium" }` — never an error that blocks ticket submission.

---

## LLM Integration

### Why Groq?

- **Completely free** — Sign up at [console.groq.com](https://console.groq.com), no credit card required. The free tier is generous enough for development and light production use.
- **Speed** — `llama-3.1-8b-instant` typically responds in 150–200ms, making it the best choice for a real-time classify call fired while the user is still typing.
- **OpenAI-compatible SDK** — The Groq Python client is a drop-in compatible with OpenAI's interface, keeping the integration simple and portable.
- **Quality** — Llama 3.1 8B follows structured JSON output instructions reliably, and `temperature=0` gives deterministic classifications.

### The Prompt

The full prompt lives in `backend/tickets/llm.py`. Key design choices:

1. **Explicit category and priority definitions** — The prompt defines each category and priority level with concrete examples, reducing ambiguous classifications.
2. **Strict JSON-only output instruction** — The model is told to respond with *only* a JSON object with no markdown fences, preamble, or explanations.
3. **Small `max_tokens` budget (64)** — Since the response is always a tiny JSON object, this prevents runaway outputs and keeps latency low.
4. **Validation after parsing** — After parsing the JSON, the code validates that both values are within the allowed choice sets before accepting them.
5. **Three-layer fallback** — `json.JSONDecodeError` → `anthropic.APIError` → generic `Exception` — each logged separately, all falling back to safe defaults.

### Error Handling Strategy

```
LLM call
  ├── No API key set          → log warning, return defaults
  ├── Invalid JSON response   → log error, return defaults
  ├── Anthropic API error     → log error, return defaults
  └── Unexpected exception    → log error, return defaults
```

The ticket form treats the classify call as fully optional — if it fails or is slow, the user simply submits with manually chosen values.

---

## Design Decisions

### Backend

- **`choices` enforced at DB level** — Django `CharField` with `choices` enforces constraints at the application layer. The migration adds `CHECK` constraints at the PostgreSQL level via Django's `CheckConstraint` (implicit in newer Django versions for `TextChoices`).
- **URL ordering** — `/api/tickets/stats/` and `/api/tickets/classify/` are registered *before* `/api/tickets/<int:pk>/` to prevent Django from trying to cast `"stats"` or `"classify"` as an integer.
- **Gunicorn in production mode** — Even in Docker, the backend runs under Gunicorn (not `manage.py runserver`) for stability.
- **DB readiness check in entrypoint** — The entrypoint polls PostgreSQL with a real connection attempt (not just a port check) before running migrations.

### Frontend

- **Debounced classify call** — The classify API is called 800ms after the user stops typing in the description field (minimum 20 characters). This avoids hammering the API on every keystroke while still feeling responsive.
- **`refreshSignal` pattern** — A simple integer counter is passed as a prop. When incremented (after ticket creation), both `TicketList` and `StatsDashboard` re-fetch their data. This avoids global state management overhead.
- **Vite proxy** — All `/api` calls in development are proxied to the backend container via Vite's built-in proxy, so the frontend never needs to know the backend's address at runtime.
- **CSS custom properties** — The entire design system uses CSS variables defined in `:root`, making theming and maintenance straightforward without a CSS framework.

---

## Environment Variables

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `GROQ_API_KEY` | backend | `""` | Your Groq API key (free at console.groq.com) |
| `DJANGO_SECRET_KEY` | backend | dev key | Django secret (change in production) |
| `DEBUG` | backend | `False` | Django debug mode |
| `POSTGRES_DB` | backend, db | `support_tickets` | Database name |
| `POSTGRES_USER` | backend, db | `postgres` | DB username |
| `POSTGRES_PASSWORD` | backend, db | `postgres` | DB password |
| `POSTGRES_HOST` | backend | `db` | DB hostname (Docker service name) |
| `POSTGRES_PORT` | backend | `5432` | DB port |

---

## Development Notes

To run the backend outside Docker (for faster iteration):

```bash
cd backend
pip install -r requirements.txt
export POSTGRES_HOST=localhost
export ANTHROPIC_API_KEY=sk-ant-...
python manage.py migrate
python manage.py runserver
```

To run the frontend outside Docker:

```bash
cd frontend
npm install
npm run dev
```

Make sure the backend is running on port 8000 for the Vite proxy to work.
