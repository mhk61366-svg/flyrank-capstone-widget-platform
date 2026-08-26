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

**Terminal output (all 12 tests above):**
```
========================================== test session starts ==========================================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3.12
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.2
collected 12 items

tests/test_submissions.py::test_valid_submission_stored PASSED                                  [  8%]
tests/test_submissions.py::test_missing_required_field_returns_422 PASSED                       [ 16%]
tests/test_submissions.py::test_invalid_email_returns_422 PASSED                                [ 25%]
tests/test_submissions.py::test_oversized_message_returns_422 PASSED                             [ 33%]
tests/test_submissions.py::test_cors_preflight_allows_configured_origin PASSED                   [ 41%]
tests/test_submissions.py::test_cors_preflight_rejects_disallowed_origin PASSED                  [ 50%]
tests/test_widgets.py::test_create_widget_requires_auth PASSED                                   [ 58%]
tests/test_widgets.py::test_create_and_get_widget PASSED                                         [ 66%]
tests/test_widgets.py::test_get_nonexistent_widget_returns_404 PASSED                             [ 75%]
tests/test_widgets.py::test_tenant_isolation_on_get_update_delete PASSED                          [ 83%]
tests/test_widgets.py::test_update_widget PASSED                                                  [ 91%]
tests/test_widgets.py::test_delete_widget PASSED                                                  [100%]

====================================== 12 passed, 1 warning in 0.63s ======================================
```