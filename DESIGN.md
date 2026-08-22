# Design Doc — Embeddable Widget & Lead-Capture Platform
**Status: SIGNED OFF — build from this.**

Repo: `flyrank-capstone-widget-platform`

---

## 1. Problem

Let an authenticated tenant create a lead-capture widget and get a one-line `<script>` snippet
to embed on any external site. Visitors on that external site submit the widget's form; the
submission must be validated, rate-limited, spam-checked, geo-enriched (with fallback), stored,
and visible to the tenant via a dashboard API, without ever trusting the origin of the request.

**Core scope only** (per brief §7 — not building the full feature set):
- 1 widget type: signup form (name, email, age, gender, optional message)
- 1 spam control: honeypot field
- Geo fallback chain: ip-api.com → ipapi.co → no geo (never blocks the submission)
- Email side effect: console log only
- "Customer site" = plain HTML file on a second local port — no real hosting/CDN

---

## 2. Data model

No local `tenants` table. Supabase Auth is the source of truth for identity — The JWT
verification (`supabase.auth.get_user()`) returns a `user.id` (UUID). That UUID is used
directly as `tenant_id` on your own tables, as a plain column — no FK, because the users
table it would reference lives in Supabase's project, not my database.

```
widgets
  id            uuid PK
  tenant_id     uuid NOT NULL         -- Supabase auth user.id, no FK (table not in this DB)
  type          text NOT NULL DEFAULT 'signup_form'
  title         text NOT NULL
  description   text
  button_text   text NOT NULL DEFAULT 'Submit'
  is_active     boolean NOT NULL DEFAULT true
  created_at    timestamptz
  updated_at    timestamptz
  -- index: (tenant_id)

submissions
  id                  uuid PK
  widget_id           uuid FK -> widgets.id
  tenant_id           uuid NOT NULL   -- denormalized from widgets.tenant_id, for fast isolation checks on read
  name                text NOT NULL
  email               text NOT NULL
  age                 int NOT NULL    -- required, confirmed
  gender              text NOT NULL   -- required, confirmed
  message             text NULL       -- optional, confirmed
  ip_address          inet
  country             text NULL
  city                text NULL
  honeypot_triggered  boolean NOT NULL DEFAULT false
  status              text NOT NULL DEFAULT 'stored'  -- 'stored' | 'rejected_spam'
  created_at          timestamptz
  -- index: (widget_id), (tenant_id, created_at)
```

**Multi-tenant isolation rule:** every query on `widgets` and `submissions` filters by
`tenant_id` taken from the verified JWT — never from a client-supplied field.

---

## 3. API surface

**Path A — Admin (authenticated, Supabase JWT required)**
```
POST   /widgets                              create widget
GET    /widgets                              list own widgets
GET    /widgets/{id}                         get one (403 if not owner's tenant)
PATCH  /widgets/{id}                         update
DELETE /widgets/{id}                         delete
GET    /widgets/{id}/submissions             list submissions (own widget only)
GET    /widgets/{id}/stats                   count / by-day / geo breakdown
```

**Path B — Public delivery (no auth, cached)**
```
GET    /widgets/{id}/config    Cache-Control: max-age=60      small JSON config
GET    /widget.js              Cache-Control: immutable, versioned URL
```

**Path C — Public submission (no auth, CORS-enabled, in-memory rate-limited)**
```
OPTIONS /submissions           preflight
POST    /submissions           validate → rate-limit → spam-check → enrich → store
```

Submission payload (draft):
```json
{
  "widget_id": "uuid",
  "name": "string",
  "email": "string",
  "age": "int",
  "gender": "string",
  "message": "string | null",
  "hp_field": ""   // honeypot — must arrive empty; humans never see/fill it
}
```

---

## 4. Layer sketch

```
HTTP (FastAPI routers)
  routes/widgets.py       — Path A
  routes/widget_public.py — Path B
  routes/submissions.py   — Path C
        │
Service layer (business logic — no SQL here)
  services/widget_service.py
  services/submission_service.py
      ├─ validation (Pydantic)
      ├─ rate_limit.py       (in-memory, per-IP + per-widget)
      ├─ spam_check.py       (honeypot)
      ├─ geo_enrichment.py   (ip-api.com → ipapi.co → none)
      └─ notify.py           (console-log side effect, failure-tolerant)
        │
Repository layer (raw SQL via psycopg — matches existing pattern, no ORM)
  repositories/widget_repo.py
  repositories/submission_repo.py
        │
PostgreSQL
```

---

## 5. Explicit non-goal

**Not building:** production CDN/hosting, bundle minification, real email delivery, more
than one widget type, CAPTCHA/proof-of-work bot defense, real-time dashboard updates, or a
local `tenants`/user table — identity is Supabase's job, not this DB's.

---

