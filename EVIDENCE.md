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

**Terminal output (all six tests above):**
```
========================================== test session starts ==========================================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3.12
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.2
collected 6 items

tests/test_widgets.py::test_create_widget_requires_auth PASSED                                 [ 16%]
tests/test_widgets.py::test_create_and_get_widget PASSED                                       [ 33%]
tests/test_widgets.py::test_get_nonexistent_widget_returns_404 PASSED                           [ 50%]
tests/test_widgets.py::test_tenant_isolation_on_get_update_delete PASSED                        [ 66%]
tests/test_widgets.py::test_update_widget PASSED                                                [ 83%]
tests/test_widgets.py::test_delete_widget PASSED                                                [100%]

====================================== 6 passed, 1 warning in 0.42s ======================================
```