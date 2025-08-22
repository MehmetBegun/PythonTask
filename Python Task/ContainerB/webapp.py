import os
import flask
import psycopg2
from datetime import datetime
import pytz

webapp = flask.Flask(__name__)

turkey_timezone = pytz.timezone('Europe/Istanbul')

def get_current_time():
    return datetime.now(tz=turkey_timezone).strftime("%Y-%m-%d %H:%M:%S")

DB_NAME = os.getenv("DB_NAME", "postgres_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

connection = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
)

@webapp.route("/")
def definition():
    page = int(flask.request.args.get('page', 1) or 1)
    per_page = int(flask.request.args.get('per_page', 100) or 100)
    q = (flask.request.args.get('q', '') or '').strip()
    sort = (flask.request.args.get('sort', 'name_asc') or 'name_asc')

    if per_page not in (20, 50, 100):
        per_page = 100

    sort_map = {
        'name_asc':  'name_surname ASC',
        'name_desc': 'name_surname DESC',
        'id_desc':   'id DESC',
        'id_asc':    'id ASC',
    }
    order_by = sort_map.get(sort, 'name_surname ASC')

    offset = (page - 1) * per_page

    cursor = connection.cursor()

    conditions = []
    params = []
    if q:
        conditions.append("(LOWER(name_surname) LIKE %s OR LOWER(nationality) LIKE %s)")
        like = f"%{q.lower()}%"
        params.extend([like, like])
    where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cursor.execute(f"SELECT COUNT(*) FROM interpol_rednotices {where_sql}", params)
    total_records = cursor.fetchone()[0]

    total_pages = (total_records + per_page - 1) // per_page if total_records else 1
    if page > total_pages:
        page = total_pages
        offset = (page - 1) * per_page

    data_sql = (
        f"SELECT id, name_surname, age, nationality, updated_at, "
        f"       (updated_at >= NOW() - INTERVAL '1 hour') AS updated_recent "
        f"FROM interpol_rednotices {where_sql} "
        f"ORDER BY {order_by} LIMIT %s OFFSET %s"
    )
    cursor.execute(data_sql, params + [per_page, offset])
    data = cursor.fetchall()

    connection.commit()
    cursor.close()

    return flask.render_template(
        "definition.html",
        data=data,
        current_time=get_current_time(),
        page=page,
        total_pages=total_pages,
        total_records=total_records,
        per_page=per_page,
        q=q,
        sort=sort,
    )

if __name__ == "__main__":
    webapp.run(host='0.0.0.0', port=5000)