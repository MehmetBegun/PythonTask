import types

class _FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql.strip(), tuple(params or [])))

    def fetchone(self):
        return (1,)

class _FakeConn:
    def __init__(self):
        self.cursor_obj = _FakeCursor()
        self.commits = 0

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

def test_postgres_repository_upsert():
    from ContainerB.consumer_db import PostgresRepository

    conn = _FakeConn()
    repo = PostgresRepository(conn)
    repo.ensure_schema()
    repo.upsert_notice("E1", "John Doe", "40 years", "USA")

    assert conn.commits >= 2
    insert_sql = [sql for (sql, _) in conn.cursor_obj.executed if sql.upper().startswith("INSERT INTO INTERPOL_REDNOTICES")]
    assert insert_sql, "Upsert SQL not executed"