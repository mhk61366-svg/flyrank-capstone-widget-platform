# Embeddable Widget & Lead-Capture Platform

Lets an authenticated tenant create a lead-capture widget and get a one-line `<script>` snippet
to embed on any external site. Visitor submissions are validated, rate-limited, spam-checked,
geo-enriched (with a provider fallback chain), stored, and exposed to the tenant via a dashboard
API — without ever trusting the origin of the request.

## Architecture

```
Widget Owner (authenticated, Supabase JWT)
  └─► Widget Management API ─► Widget DB (tenant-isolated) ─► embed snippet returned in response

Customer Website (any origin)
  └─ <script src="widget.js?id=abc123">
        └─► GET /widgets/:id/config   (public · cached 60s · CORS)
        └─► render widget

Website Visitor
  └─► POST /submissions   (public · CORS)
        ├─► validation (Pydantic) ── bad payload? → 4xx, never 500
        ├─► rate limit + honeypot spam check ── flood/bot? → 429 / rejected_spam, service stays up
        ├─► geo enrichment: ip-api.com ─(fails)─► ipapi.co ─(fails)─► store anyway, no geo
        ├─► store submission
        └─► console-log confirmation (failure never blocks the response)

Widget Owner (authenticated)
  └─► Dashboard API ◄── submissions + stats (counts, by-day, by-country)
```

**Layers:** `routes/` (HTTP, FastAPI) → `services/` (business logic, no SQL) → `repositories/`
(raw SQL via psycopg, no ORM) → PostgreSQL. Identity is Supabase Auth's job — this database has
no local `tenants` table; the verified JWT's `user.id` is used directly as `tenant_id`.

## Setup

1. Clone this repo
2. Copy `.env.example` to `.env` and fill in your Supabase project's URL and publishable key
3. `docker compose up -d --build`
4. Run tests: `docker compose exec api pytest -v`
5. *(Optional)* Seed the fixed demo widget for the public endpoints:
  `docker compose exec api python -m app.seed` — this only creates data reachable via the public
  routes (`/config`, `/submissions`); the admin routes still require your own Supabase user (see
  Limitations). The manual curl and direct database checks for the seeded widget are recorded in
  [EVIDENCE.md].

## API documentation

Full interactive docs (via FastAPI's auto-generated OpenAPI UI): `http://localhost:8000/docs`

| Route | Auth | Purpose |
|---|---|---|
| `POST /widgets` | JWT | Create a widget |
| `GET /widgets` | JWT | List your widgets |
| `GET/PATCH/DELETE /widgets/{id}` | JWT | Manage one widget (404 if not yours) |
| `GET /widgets/{id}/submissions` | JWT | List submissions for a widget you own |
| `GET /widgets/{id}/stats` | JWT | Counts, by-day, by-country breakdown |
| `GET /widgets/{id}/config` | none | Public widget config (cached 60s) |
| `GET /widget.js` | none | Embed script (cached immutable) |
| `POST /submissions` | none, CORS | Public submission endpoint |

## Known limitations

- Auth is JWT verification on protected routes only — no signup/login flow, no RLS policies;
  identity and account creation are entirely Supabase's responsibility, per design.
- The customer-site widget submission only works when your API is running locally on the same
  machine viewing the page — there's no public hosting of the API, so a real third-party visitor
  to a deployed customer site cannot submit the form. This is expected for the capstone's $0/
  no-hosting scope, not a bug.
- Making this work from a real HTTPS-hosted customer site (verified against a live Netlify page)
  additionally required handling Chrome's Private Network Access restriction, which blocks any
  public-origin page from fetching a `localhost` target unless the server explicitly opts in via
  an `Access-Control-Allow-Private-Network` response header — this is separate from, and stricter
  than, ordinary CORS origin checks, and is implemented as its own middleware.
- Rate limiting is per-IP only, in-memory (resets on API restart) — no distributed store.
- Found and fixed during testing, not present in the shipped code: an early version of
  `ALLOWED_ORIGINS` had a trailing-slash mismatch against the browser's real `Origin` header,
  and the CORS/Private-Network middleware ordering initially made the private-network fix
  unreachable for preflight requests. Both are corrected; see EVIDENCE.md for detail.