import uuid
from datetime import datetime, timezone

def row_to_dict(cur, row):
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))

def insert(conn, *, widget_id, tenant_id, name, email, age, gender, message,
           ip_address, country, city, honeypot_triggered, status):
    submission_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO submissions
                (id, widget_id, tenant_id, name, email, age, gender, message,
                 ip_address, country, city, honeypot_triggered, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (submission_id, widget_id, tenant_id, name, email, age, gender, message,
             ip_address, country, city, honeypot_triggered, status, now),
        )
        return row_to_dict(cur, cur.fetchone())


