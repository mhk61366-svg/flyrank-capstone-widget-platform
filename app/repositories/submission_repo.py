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

def list_for_widget(conn, widget_id: str, tenant_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM submissions WHERE widget_id = %s AND tenant_id = %s ORDER BY created_at DESC",
            (widget_id, tenant_id),
        )
        rows = cur.fetchall()
        return [row_to_dict(cur, r) for r in rows]


def stats_for_widget(conn, widget_id: str, tenant_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM submissions WHERE widget_id=%s AND tenant_id=%s AND status='stored'",
            (widget_id, tenant_id),
        )
        total_stored = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM submissions WHERE widget_id=%s AND tenant_id=%s AND status='rejected_spam'",
            (widget_id, tenant_id),
        )
        total_spam_blocked = cur.fetchone()[0]

        cur.execute(
            """
            SELECT created_at::date AS day, COUNT(*) FROM submissions
            WHERE widget_id=%s AND tenant_id=%s AND status='stored'
            GROUP BY day ORDER BY day
            """,
            (widget_id, tenant_id),
        )
        by_day = [{"date": str(row[0]), "count": row[1]} for row in cur.fetchall()]

        cur.execute(
            """
            SELECT country, COUNT(*) FROM submissions
            WHERE widget_id=%s AND tenant_id=%s AND status='stored' AND country IS NOT NULL
            GROUP BY country ORDER BY COUNT(*) DESC
            """,
            (widget_id, tenant_id),
        )
        by_country = [{"country": row[0], "count": row[1]} for row in cur.fetchall()]

        return {
            "total_stored": total_stored,
            "total_spam_blocked": total_spam_blocked,
            "by_day": by_day,
            "by_country": by_country,
        }


