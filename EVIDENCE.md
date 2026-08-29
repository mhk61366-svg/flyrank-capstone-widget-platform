## Widget Management (2a)

### ✅ Authenticated CRUD endpoints — requests without valid auth are rejected

**Test:** `test_create_widget_requires_auth`
**Command:** `docker compose exec api pytest -v`

Missing `Authorization` header returns `401`, not a crash (previously returned `422` — fixed by
changing `Header(...)` to `Header(None)` in `auth.py` with a manual check, since a required
`Header(...)` triggers FastAPI's request-validation layer before the auth logic ever runs).

### ✅ Multi-tenant isolation proven — tenant A cannot read or modify tenant B's widgets

**Test:** `test_tenant_isolation_on_get_update_delete`
**Command:** `docker compose exec api pytest -v`

Tenant B's client attempts `GET`, `PATCH`, and `DELETE` on a widget created by tenant A. All three
return `404` (chosen over `403` — see design decision below).

**Design decision:** DESIGN.md originally specified `403 Forbidden` for a widget owned by another
tenant. Switched to `404 Not Found` because a `403` confirms to an attacker that the widget ID
exists and merely belongs to someone else, while a `404` reveals nothing about existence. DESIGN.md
§3 updated to match.

### ✅ Full CRUD, validated, honest status codes

**Tests:** `test_create_and_get_widget`, `test_get_nonexistent_widget_returns_404`,
`test_update_widget`, `test_delete_widget`
**Command:** `docker compose exec api pytest -v`

Create → `201` with `id`; get → `200`; get nonexistent → `404`; update → `200` with updated field;
delete → `204`, and a subsequent get on the deleted widget returns `404`.

---

## Public Submission API (2b)

### ✅ All incoming input validated; malformed payloads rejected with clean 4xx, never 500

**Tests:** `test_valid_submission_stored`, `test_missing_required_field_returns_422`,
`test_invalid_email_returns_422`, `test_oversized_message_returns_422`
**Command:** `docker compose exec api pytest -v`

Valid submission → `201` with `status: "stored"`. Missing `age`, an invalid email format, and an
oversized `message` (>2000 chars) each return `422` with a structured Pydantic validation error,
never a raw crash.

### ✅ Cross-origin submissions work: CORS headers correct, preflight (OPTIONS) handled

**Tests:** `test_cors_preflight_allows_configured_origin`, `test_cors_preflight_rejects_disallowed_origin`
**Command:** `docker compose exec api pytest -v`

A preflight `OPTIONS` request from the configured origin (`http://localhost:5500`) returns `200`
with a matching `access-control-allow-origin` header. A preflight from an unconfigured origin
(`http://evil.com`) returns no `access-control-allow-origin` header at all — proving the CORS
middleware restricts by origin rather than allowing everything (`*`).


## Abuse Protection & Spam Control (2c)

### ✅ Rate limiting per IP returns 429 under a burst, and the API keeps serving legitimate traffic after

**Tests:** `test_rate_limit_returns_429_after_burst`, `test_normal_request_succeeds_after_rate_limit_window`
**Command:** `docker compose exec api pytest -v`

Firing 15 rapid submission requests from the test client returns `201` for the requests within
the configured limit, then `429 Too Many Requests` once the per-IP threshold is crossed. A
second test then confirms the API recovers rather than staying locked out: after the burst, the
limiter's window is reset and the very next request returns `201` again.

**Caveat, stated plainly rather than glossed over:** the recovery test does not wait for
slowapi's real time-based window to expire — it calls `limiter.reset()` directly to force the
limiter back into a fresh-window state. This proves the *endpoint's behavior once the window has
passed* (a normal request succeeds, nothing is left permanently blocked), but it does not test
slowapi's actual clock-based expiry mechanism itself, since waiting out a real 60-second window
inside an automated test suite isn't practical. If asked, the honest answer is: the reset is
simulated, not timed.

### ✅ At least one spam-prevention technique demonstrably blocks a spam submission

**Test:** `test_honeypot_filled_marks_rejected_spam`
**Command:** `docker compose exec api pytest -v`

A submission with a non-empty `hp_field` (the honeypot — real users never see or fill it; only a
bot blindly filling every input would) is stored with `status: "rejected_spam"` and
`honeypot_triggered: true`, rather than being treated as a normal lead. The check is
presence-based, not keyword-based — any non-empty value trips it, not specific bot-like text.

### Bug fixed during this phase: client IP rejected by Postgres under automated tests

FastAPI's `TestClient` doesn't make a real network connection, so `request.client.host` returns
the literal string `"testclient"` instead of a real IP. The `submissions.ip_address` column is
typed `inet`, which does strict validation and rejected that string outright
(`psycopg.errors.InvalidTextRepresentation`), causing three tests
(`test_valid_submission_stored`, `test_honeypot_filled_marks_rejected_spam`,
`test_rate_limit_returns_429_after_burst`) to fail with a DB-layer error rather than an
application-logic error.

**Fix:** added `safe_ip()` in `app/services/submission_service.py`, which validates the incoming
string against `ipaddress.ip_address()` and returns `None` for anything that isn't a real IP,
before it reaches the repository/SQL layer. This also hardens the endpoint against a real-world
edge case — some reverse-proxy configurations leave `request.client` as `None` — not just the
test artifact.

**Tests:** `test_normalize_ip_accepts_valid_ip`, `test_normalize_ip_rejects_garbage`
**Command:** `docker compose exec api pytest -v`

A valid IP string (`8.8.8.8`) passes through unchanged; `"testclient"` and `None` both resolve to
`None`, which the `inet` column accepts as `NULL`.


## Geo Enrichment & Provider Fallback (2d)

### ✅ Geo enrichment uses the first provider directly when it succeeds, without calling the second

**Test:** `test_geo_enrichment_uses_first_provider_when_available`
**Command:** `docker compose exec api pytest -v -k geo_enrichment`

The first provider is mocked to return real-looking data; the second provider is mocked to raise
an `AssertionError` if called at all. The test passes, proving the fallback chain short-circuits
correctly and never wastes a call to the second provider when the first one already answered —
without this test, a bug that always called both providers regardless of the first result would
go undetected.

### ✅ Geo enrichment falls back to the second provider when the first is unavailable

**Test:** `test_geo_enrichment_falls_back_to_second_provider`
**Command:** `docker compose exec api pytest -v -k geo_enrichment`

The first provider is mocked as unavailable and the second provider returns `Testland` / `Testville`.
The fallback chain returns the second provider's result without making a real network request.

### ✅ Geo enrichment degrades safely when both providers are unavailable

**Test:** `test_geo_enrichment_returns_none_when_both_providers_down`
**Command:** `docker compose exec api pytest -v -k geo_enrichment`

When both providers are mocked as unavailable, enrichment returns `country: None` and `city: None`
rather than raising an error.

### ✅ Submission still succeeds when both geo providers are unavailable

**Test:** `test_submission_succeeds_when_both_geo_providers_down`
**Command:** `docker compose exec api pytest -v -k geo`

The submission endpoint returns `201` with `status: "stored"` even when both geo providers fail,
proving that enrichment degrades without blocking valid submissions.

### ✅ Manual real-network geo enrichment confirmed working

**Command:** `docker compose exec db psql -U widgetuser -d widgetdb -c "SELECT country, city, ip_address FROM submissions ORDER BY created_at DESC LIMIT 1;"`

**Note on reading this evidence:** `ip_address` and the IP passed into `geo_enrichment.enrich()`
are two independently-stored values in this codebase — `ip_address` always reflects the real
caller (here, the internal Docker gateway `172.18.0.1`, since the request came from inside the
Docker network), while the geo lookup itself was temporarily pointed at a real public IP
(`8.8.8.8`) purely to confirm the provider APIs return live data. The mismatch between the two
columns below is expected, not a data inconsistency.

To confirm real provider enrichment works, `geo_enrichment.enrich()`'s call site was temporarily
hardcoded to a public IP (`8.8.8.8`):
```text
country       |  city   | ip_address
--------------+---------+------------
United States | Ashburn | 172.18.0.1
(1 row)
```

After reverting the hardcode, a submission through the real endpoint (real caller IP,
`172.18.0.1`, an internal/non-routable address with no geo data) correctly stores empty geo
fields rather than crashing or returning stale data:
```text
country | city | ip_address
--------+------+-------------
        |      | 172.18.0.1
(1 row)
```

The first output proves real provider enrichment returns data over the live network; the second
confirms the endpoint degrades safely (stores `NULL` geo fields, no error) once the hardcode is
removed and a real, non-geolocatable IP is used.

---

## Safe Side Effect — Notify (2e)

### ✅ A failing confirmation email/webhook does not prevent the submission from being stored

**Test:** `test_submission_succeeds_even_if_notify_raises`
**Command:** `docker compose exec api pytest -v`

`notify.send_confirmation` is mocked to raise `RuntimeError("SMTP is down")`. The submission
endpoint still returns `201` with `status: "stored"` — the failure is caught and logged
(`[NOTIFY ERROR] ...`) inside `create_submission`'s own `try/except Exception` boundary, never
propagating up to break the response. This is the one place in the codebase where catching a
bare `Exception` is intentional rather than lazy: it's the explicit "this must never take down
the main path" boundary the brief calls out under Probe 5.

### ✅ Notify is actually invoked on a normal, successful submission

**Test:** `test_notify_called_on_successful_submission`
**Command:** `docker compose exec api pytest -v`

`notify.send_confirmation` is mocked to record its arguments instead of printing. A normal
submission triggers the mock with the correct email and widget ID, proving the side effect
genuinely fires on the happy path — not just that failures are survivable. Without this test,
deleting the `notify.send_confirmation(...)` call entirely would have left every other test
passing, since the failure test alone only proves *robustness*, not that the call happens.

**Bug caught by writing this test:** `create_submission` was calling
`notify.send_confirmation(data.email, str(widget_id))` — referencing a bare `widget_id` name
that doesn't exist in that function's scope (the parameter is `data`, and the ID is
`data.widget_id`). This raised a `NameError` on every single submission, silently swallowed by
the same `try/except Exception` block designed to protect against exactly this kind of failure.
Every prior "PASSED" for notify-related tests had passed by coincidence, not because
`send_confirmation` ever ran successfully. Fixed to
`notify.send_confirmation(data.email, str(data.widget_id))`.

## Phase 2 gaps closed before Phase 3 (0)

### ✅ Actual submission response carries correct CORS headers, not just the preflight

**Tests:** `test_actual_post_response_has_cors_header_for_allowed_origin`,
`test_actual_post_response_has_no_cors_header_for_disallowed_origin`
**Command:** `docker compose exec api pytest -v`

The earlier CORS tests (2b) only checked the `OPTIONS` preflight response. Preflight and the
real request's response are headered independently by `CORSMiddleware`, so passing preflight
doesn't guarantee the actual `POST` response is correct too. These two tests close that gap:
a request from the allowed origin gets a matching `access-control-allow-origin` header on the
real response; a request from a disallowed origin gets none.

### Dependency update: `httpx2`

Starlette's `TestClient` deprecated its use of plain `httpx` in favor of `httpx2` (maintained by
Pydantic's team, since `httpx` itself is unmaintained). Added `httpx2` to `requirements.txt`;
the `StarletteDeprecationWarning` seen in the Phase 2c terminal output is gone as of this commit.

```
**Terminal output (full suite, end of Phase 2):**
```
========================================= test session starts =========================================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3.12
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.2
collected 25 items

tests/test_submissions.py::test_normalize_ip_accepts_valid_ip PASSED                              [  4%]
tests/test_submissions.py::test_normalize_ip_rejects_garbage PASSED                               [  8%]
tests/test_submissions.py::test_valid_submission_stored PASSED                                    [ 12%]
tests/test_submissions.py::test_missing_required_field_returns_422 PASSED                         [ 16%]
tests/test_submissions.py::test_invalid_email_returns_422 PASSED                                  [ 20%]
tests/test_submissions.py::test_oversized_message_returns_422 PASSED                              [ 24%]
tests/test_submissions.py::test_cors_preflight_allows_configured_origin PASSED                    [ 28%]
tests/test_submissions.py::test_cors_preflight_rejects_disallowed_origin PASSED                   [ 32%]
tests/test_submissions.py::test_honeypot_filled_marks_rejected_spam PASSED                        [ 36%]
tests/test_submissions.py::test_rate_limit_returns_429_after_burst PASSED                         [ 40%]
tests/test_submissions.py::test_normal_request_succeeds_after_rate_limit_window PASSED            [ 44%]
tests/test_submissions.py::test_geo_enrichment_uses_first_provider_when_available PASSED          [ 48%]
tests/test_submissions.py::test_geo_enrichment_falls_back_to_second_provider PASSED               [ 52%]
tests/test_submissions.py::test_geo_enrichment_returns_none_when_both_providers_down PASSED       [ 56%]
tests/test_submissions.py::test_submission_succeeds_when_both_geo_providers_down PASSED           [ 60%]
tests/test_submissions.py::test_submission_succeeds_even_if_notify_raises PASSED                  [ 64%]
tests/test_submissions.py::test_notify_called_on_successful_submission PASSED                     [ 68%]
tests/test_submissions.py::test_actual_post_response_has_cors_header_for_allowed_origin PASSED    [ 72%]
tests/test_submissions.py::test_actual_post_response_has_no_cors_header_for_disallowed_origin PASSED [ 76%]
tests/test_widgets.py::test_create_widget_requires_auth PASSED                                    [ 80%]
tests/test_widgets.py::test_create_and_get_widget PASSED                                          [ 84%]
tests/test_widgets.py::test_get_nonexistent_widget_returns_404 PASSED                             [ 88%]
tests/test_widgets.py::test_tenant_isolation_on_get_update_delete PASSED                          [ 92%]
tests/test_widgets.py::test_update_widget PASSED                                                  [ 96%]
tests/test_widgets.py::test_delete_widget PASSED                                                  [100%]

========================================== 25 passed in 1.81s ==========================================

## Widget Delivery (3a)

### ✅ Embed snippet generated per widget

**Verified via:** Postman — `POST /widgets` and `GET /widgets/{id}` responses

No automated test for this specifically — `embed_snippet` is a deterministic string built from
`API_BASE_URL`, the widget's own `id`, and `WIDGET_JS_VERSION`, not business logic with edge
cases worth unit testing. Confirmed present and correctly formatted in the response body:
`"embed_snippet": "<script src=\"http://localhost:8000/widget.js?id=1111c50e-3f2a-42d5-85a2-83f6b5ebcee7&v=1\"></script>"`.

### ✅ Public config endpoint serves a small payload with correct HTTP cache headers, no tenant leak

**Tests:** `test_config_returns_cache_header_and_no_tenant_id`, `test_config_404_for_nonexistent_widget`
**Command:** `docker compose exec api pytest -v tests/test_widget_public.py`

`GET /widgets/{id}/config` returns `200` with `Cache-Control: public, max-age=60` and a small
JSON body (`title`, `description`, `button_text`) — `tenant_id` is deliberately absent, since
this is a public endpoint any anonymous visitor's browser can call. A nonexistent widget ID
returns `404`, not a crash or an empty success response.

### ✅ Widget JavaScript is served as a versioned bundle with correct cache headers

**Test:** `test_widget_js_served_with_immutable_cache_header`
**Command:** `docker compose exec api pytest -v tests/test_widget_public.py`

`GET /widget.js` returns `200`, `Content-Type: application/javascript`, and
`Cache-Control: public, max-age=31536000, immutable`. Versioning is via a `?v=` query parameter
(bumped manually in `WIDGET_JS_VERSION` when the file changes) rather than a content-hashed
filename — simpler, and sufficient to satisfy "new version = new URL or cache-bust" per the brief.

### Bug fixed during this phase: `Cache-Control` header silently dropped on `/widget.js`

FastAPI's pattern of injecting a `Response` object and mutating `response.headers[...]` only
takes effect when the route function returns plain data (a dict/list/model) that FastAPI wraps
into a response itself. `get_widget_js` instead explicitly constructed and returned its own
`Response(...)` object — FastAPI sends that object as-is and never applies the injected
parameter's header mutation, so `Cache-Control` was silently missing from every response despite
the code appearing to set it. Confirmed via Postman: `Content-Type` and body were correct, but
the Headers tab showed no `Cache-Control` at all.

**Fix:** pass `headers={"Cache-Control": "..."}` directly into the `Response(...)` constructor
being returned, instead of mutating a separate injected `response` parameter that was never
actually being sent.

**Terminal output:**
```
========================================== test session starts ==========================================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3.12
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.14.2
collected 3 items

tests/test_widget_public.py::test_config_returns_cache_header_and_no_tenant_id PASSED             [ 33%]
tests/test_widget_public.py::test_config_404_for_nonexistent_widget PASSED                        [ 66%]
tests/test_widget_public.py::test_widget_js_served_with_immutable_cache_header PASSED             [100%]

=========================================== 3 passed in 0.21s ===========================================

```

## Customer-Site Test Page & Cross-Origin Embed (3b)

### ✅ Widget renders on a page served from a different origin, and a real submission is stored end-to-end

**Verified via:** manual browser test (not automated — see honest scope note below).
`customer-site/index.html` served on `http://localhost:5500` via `python -m http.server 5500`,
loading the embed snippet pointed at the API running on `http://localhost:8000`. Two genuinely
different origins (different ports), which is what actually triggers real browser CORS
enforcement — not a local trick standing in for it.

In a real browser: the widget form rendered correctly (all five fields — name, email, age,
gender, message — plus the hidden honeypot), was filled in and submitted, and the page displayed
"Thanks! We got your submission." DevTools' Network tab showed the `OPTIONS` preflight followed
by the real `POST`, both succeeding.

**Confirmed the submission actually persisted, not just that the UI looked successful:**

**Command:**
 docker compose exec db psql -U widgetuser -d widgetdb -c "SELECT name, email, status, created_at FROM submissions ORDER BY created_at DESC LIMIT 1;


**Output:**

  name  |      email       | status |          created_at           
--------+------------------+--------+-------------------------------
 Farhan | farhan@gmail.com | stored | 2026-08-28 13:08:21.341625+00

A real row, with the values actually typed into the browser form, and `status: stored` — proving
the full path (render → cross-origin submit → validate → store) worked, not just that the page
displayed a friendly message.

**Honest scope note:** "widget renders on a second-origin page" is verified manually here, by
eye and by DB query — not by an automated headless-browser test (Playwright/Selenium). That
would be a new tool with real setup cost not otherwise needed by this project; a manual,
documented verification is a legitimate way to satisfy this requirement, it's just not
mechanically re-runnable the way the pytest suite is. Stated plainly rather than implied
otherwise.

**Browser console noise, unrelated to the app — noted so it isn't mistaken for a bug:** two 404s
appeared during this test (`favicon.ico` and `.well-known/appspecific/com.chrome.devtools.json`).
Both are automatic browser/DevTools requests unrelated to `customer-site/index.html` or the API;
neither reflects an application error.

### ✅ Widget renders and submits successfully from a real, independently-hosted origin

**Manual verification** — real browser, real deployed site, not `TestClient`
**Setup:** embed script added to a live Netlify-hosted page (`https://7wondersworld.netlify.app`),
`ALLOWED_ORIGINS` updated to include the real Netlify domain.

**Two real bugs found and fixed during this check, not caught by any automated test so far:**

1. **Private Network Access (PNA) block.** Chrome refused the request entirely with "blocked by
   CORS policy: Permission was denied for this request to access the loopback address space" —
   a stricter, separate browser restriction (not ordinary CORS) that blocks any public `https://`
   origin from fetching a `localhost`/loopback target. Fixed by adding a custom
   `PrivateNetworkMiddleware` that echoes `Access-Control-Allow-Private-Network: true` on
   preflight requests carrying `Access-Control-Request-Private-Network`. This only works because
   the browser and the API happen to run on the same machine during dev/demo; a real third-party
   visitor still could not reach `localhost:8000`, which is a stated, accepted limitation of this
   capstone's $0/no-hosting scope (see README limitations).

2. **Trailing-slash origin mismatch.** `ALLOWED_ORIGINS` in `.env` had
   `https://7wondersworld.netlify.app/` (trailing slash); the browser's real `Origin` header is
   sent without one. `CORSMiddleware` does an exact string match, so this silently failed CORS
   with "No 'Access-Control-Allow-Origin' header is present" until the trailing slash was
   removed.

**Command:**
```
docker compose exec api python -c "from app.config import ALLOWED_ORIGINS; print(ALLOWED_ORIGINS)"
```
['http://localhost:5500', 'https://7wondersworld.netlify.app']


**Result:** widget config loads, form renders on the live page, and a real submission from that
page lands in the database.

**Command:**

docker compose exec db psql -U widgetuser -d widgetdb -c "SELECT id, widget_id, name, email, country, city, created_at FROM submissions ORDER BY created_at DESC LIMIT 3;"

**Output**

                  id                  |              widget_id               |  name  |         email         | country | city |          created_at           
--------------------------------------+--------------------------------------+--------+-----------------------+---------+------+-------------------------------
 92c7bb14-8de8-480d-a557-f4efbfefaa9b | 79ff7422-46ca-4e83-8dba-5693b01b4d1d | saad   | saad@gmail.com        |         |      | 2026-08-28 15:01:16.889037+00
 dc2520a5-0b21-4152-be06-dde138deb8e3 | 48b28b72-e133-43fd-9c8c-0a3cec4b0f68 | Farhan | farhan@gmail.com      |         |      | 2026-08-28 13:08:21.341625+00
 319540b0-d253-48b8-abb6-89cc1976d1c6 | 92ca3669-2b59-40ce-b429-31d789efc53f | Test   | emamartinez@gmail.com |         |      | 2026-08-28 06:37:50.129242+00
(3 rows)
:

## Dashboard API (3d)

**Scope note:** dashboard endpoints aren't individually listed as Definition-of-Done checkboxes
in the brief — Probe 1 only requires a submission be "visible via the dashboard API," nothing
stricter. The tests below go beyond that minimum (tenant isolation, spam exclusion, empty-state
handling, geo/day aggregation specifically) — not strictly required, but proving the endpoints
are correct rather than merely present.

### ✅ Widget owner can view their submissions and stats; spam tracked separately, not counted as a lead

**Tests:** `test_submissions_list_returns_all_rows_for_owner`, `test_stats_excludes_spam_from_stored_count`
**Command:** `docker compose exec api pytest -v tests/test_dashboard.py`

`GET /widgets/{id}/submissions` returns all rows for the widget, including spam. `GET
/widgets/{id}/stats` reports `total_stored` and `total_spam_blocked` as separate counts — a
honeypot-caught submission is never counted as a real lead, but is still visible as a caught-spam
number, not silently discarded.

### ✅ Dashboard endpoints require authentication and enforce tenant isolation

**Tests:** `test_dashboard_endpoints_require_auth`, `test_dashboard_endpoints_reject_other_tenant`
**Command:** `docker compose exec api pytest -v tests/test_dashboard.py`

An unauthenticated request to either endpoint returns `401`. A request from a tenant that doesn't
own the widget returns `404` (same isolation pattern as widget CRUD in 2a — existence is never
revealed to a non-owner).

**Bug found and fixed while writing these tests:** `dependency_overrides` on `get_current_tenant_id`
is a single dictionary shared by the whole `app` object, not scoped per `TestClient`. The original
`tenant_a_client`/`tenant_b_client` fixtures set this override and only cleared it at fixture
teardown — meaning when a test needed *two* different tenant identities active across a single
test (something no earlier test in this project required), the override from one fixture silently
persisted or got overwritten by another, causing `test_dashboard_endpoints_require_auth` and
`test_dashboard_endpoints_reject_other_tenant` to both incorrectly return `200` instead of `401`/
`404` — the "unauthenticated" and "tenant B" clients were secretly still authenticated as tenant A.
**Fix:** replaced the fixtures with an `as_tenant(tenant_id)` context manager (in `conftest.py`)
that sets the override and clears it immediately around each individual request, so no identity
ever leaks past the exact block that needs it.

### ✅ Stats handle the empty case correctly, and geo/day breakdowns aggregate correctly

**Tests:** `test_stats_and_submissions_empty_for_widget_with_no_submissions`, `test_stats_includes_geo_breakdown`
**Command:** `docker compose exec api pytest -v tests/test_dashboard.py`

A brand-new widget with zero submissions returns an empty list and empty stats rather than
erroring on an empty result set. Geo enrichment is mocked deterministically (same pattern as the
Phase 2d fallback tests) to verify `by_country` and `by_day` correctly aggregate real data — this
automates the same check originally done manually in Phase 3d.2 by temporarily hardcoding a real
public IP and eyeballing the response.

**Terminal output:**
```
========================================== test session starts ==========================================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3.12
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.14.2
collected 6 items

tests/test_dashboard.py::test_submissions_list_returns_all_rows_for_owner PASSED             [ 16%]
tests/test_dashboard.py::test_stats_excludes_spam_from_stored_count PASSED                   [ 33%]
tests/test_dashboard.py::test_dashboard_endpoints_require_auth PASSED                        [ 50%]
tests/test_dashboard.py::test_dashboard_endpoints_reject_other_tenant PASSED                 [ 66%]
tests/test_dashboard.py::test_stats_and_submissions_empty_for_widget_with_no_submissions PASSED [ 83%]
tests/test_dashboard.py::test_stats_includes_geo_breakdown PASSED                            [100%]

============================================ 6 passed in 0.58s ============================================
```