import uuid
from datetime import datetime, timezone
from app.config import DATABASE_URL
from app.db import get_db
from contextlib import contextmanager
from app.db import get_db as _get_db_gen

SEED_TENANT_ID = "00000000-0000-0000-0000-000000000001"
SEED_WIDGET_ID = "00000000-0000-0000-0000-0000000000aa"

get_db_context = contextmanager(_get_db_gen)

def run():
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM widgets WHERE id = %s", (SEED_WIDGET_ID,))
            if cur.fetchone():
                print(f"[SEED] Demo widget already exists: {SEED_WIDGET_ID}")
                return
            now = datetime.now(timezone.utc)
            cur.execute(
                """
                INSERT INTO widgets (id, tenant_id, type, title, description, button_text, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (SEED_WIDGET_ID, SEED_TENANT_ID, "signup_form", "Demo Signup Widget",
                 "Seeded demo widget — public endpoints only, see README limitations", "Submit",
                 True, now, now),
            )
        conn.commit()
    print(f"[SEED] Demo widget created: {SEED_WIDGET_ID}")
    print(f"[SEED] Test with:")
    print(f"  curl http://localhost:8000/widgets/{SEED_WIDGET_ID}/config")
    print(f"  curl -X POST http://localhost:8000/submissions -H 'Content-Type: application/json' \\")
    print(f"    -d '{{\"widget_id\":\"{SEED_WIDGET_ID}\",\"name\":\"Test\",\"email\":\"a@b.com\",\"age\":25,\"gender\":\"f\"}}'")

if __name__ == "__main__":
    run()