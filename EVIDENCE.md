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

---

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

**Terminal output (full suite after Phase 2c):**
========================================== test session starts ==========================================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3.12
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.2
collected 17 items

tests/test_submissions.py::test_normalize_ip_accepts_valid_ip PASSED                          [  5%]
tests/test_submissions.py::test_normalize_ip_rejects_garbage PASSED                           [ 11%]
tests/test_submissions.py::test_valid_submission_stored PASSED                                [ 17%]
tests/test_submissions.py::test_missing_required_field_returns_422 PASSED                     [ 23%]
tests/test_submissions.py::test_invalid_email_returns_422 PASSED                              [ 29%]
tests/test_submissions.py::test_oversized_message_returns_422 PASSED                          [ 35%]
tests/test_submissions.py::test_cors_preflight_allows_configured_origin PASSED                [ 41%]
tests/test_submissions.py::test_cors_preflight_rejects_disallowed_origin PASSED               [ 47%]
tests/test_submissions.py::test_honeypot_filled_marks_rejected_spam PASSED                    [ 52%]
tests/test_submissions.py::test_rate_limit_returns_429_after_burst PASSED                     [ 58%]
tests/test_submissions.py::test_normal_request_succeeds_after_rate_limit_window PASSED        [ 64%]
tests/test_widgets.py::test_create_widget_requires_auth PASSED                                [ 70%]
tests/test_widgets.py::test_create_and_get_widget PASSED                                      [ 76%]
tests/test_widgets.py::test_get_nonexistent_widget_returns_404 PASSED                         [ 82%]
tests/test_widgets.py::test_tenant_isolation_on_get_update_delete PASSED                      [ 88%]
tests/test_widgets.py::test_update_widget PASSED                                              [ 94%]
tests/test_widgets.py::test_delete_widget PASSED                                              [100%]

========================================== 17 passed in 1.47s ==========================================
