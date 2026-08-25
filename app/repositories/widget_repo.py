import uuid
from datetime import datetime, timezone

def row_to_dict(cur, row):
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))

def create(conn, tenant_id: str, title: str, description: str | None, button_text: str):
    widget_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO widgets (id, tenant_id, title, description, button_text, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (widget_id, tenant_id, title, description, button_text, now, now),
        )
        return row_to_dict(cur, cur.fetchone())


def list_for_tenant(conn, tenant_id: str):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM widgets WHERE tenant_id = %s ORDER BY created_at DESC", (tenant_id,))
        rows = cur.fetchall()
        return [row_to_dict(cur, r) for r in rows]

def get_owned(conn, widget_id: str, tenant_id: str):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM widgets WHERE id = %s AND tenant_id = %s", (widget_id, tenant_id))
        row = cur.fetchone()
        return row_to_dict(cur, row) if row else None


def update_owned(conn, widget_id: str, tenant_id: str, fields: dict):
    if not fields:
        return get_owned(conn, widget_id, tenant_id)
    fields["updated_at"] = datetime.now(timezone.utc)
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE widgets SET {set_clause} WHERE id = %s AND tenant_id = %s RETURNING *",
            (*fields.values(), widget_id, tenant_id),
        )
        row = cur.fetchone()
        return row_to_dict(cur, row) if row else None

def delete_owned(conn, widget_id: str, tenant_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM widgets WHERE id = %s AND tenant_id = %s RETURNING id", (widget_id, tenant_id))
        return cur.fetchone() is not None

def get_by_id(conn, widget_id: str):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM widgets WHERE id = %s", (widget_id,))
        row = cur.fetchone()
        return row_to_dict(cur, row) if row else None