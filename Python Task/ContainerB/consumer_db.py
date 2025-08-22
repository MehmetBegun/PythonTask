import pika
import time
import json
import psycopg2
import os

i = 0

class PostgresRepository:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def ensure_schema(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS interpol_rednotices (
                id SERIAL PRIMARY KEY,
                entity_id VARCHAR(128) UNIQUE,
                name_surname VARCHAR(200) NOT NULL,
                age VARCHAR(100),
                nationality VARCHAR(120) NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """
        )
        self.cursor.execute("ALTER TABLE interpol_rednotices ADD COLUMN IF NOT EXISTS entity_id VARCHAR(128);")
        self.cursor.execute("ALTER TABLE interpol_rednotices ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW();")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_interpol_entity ON interpol_rednotices (entity_id);")
        self.connection.commit()

    def upsert_notice(self, entity_id, name, age, nationality):
        self.cursor.execute(
            """
            INSERT INTO interpol_rednotices (entity_id, name_surname, age, nationality)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (entity_id)
            DO UPDATE SET name_surname = EXCLUDED.name_surname,
                          age = EXCLUDED.age,
                          nationality = EXCLUDED.nationality,
                          updated_at = NOW();
            """,
            (entity_id, name, age, nationality),
        )
        self.connection.commit()

class QueueConsumer:
    def __init__(self, repository: PostgresRepository):
        self.repository = repository

    def _callback(self, ch, method, properties, body):
        print(f"New message has been pushed:\n{body}\n")
        global i
        try:
            data = json.loads(body)
        except Exception:
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception as e:
                print(f"Invalid message, skipping: {e}")
                return
        entity_id = data.get("EntityId")
        name = data.get("Name")
        age = data.get("Age")
        nationality = data.get("Nationalities")
        i += 1
        self.repository.upsert_notice(entity_id, name, age, nationality)

    def start(self):
        max_retries = 10
        retry_count = 0
        while retry_count < max_retries:
            try:
                rabbit_host = os.getenv("RABBITMQ_HOST", "container_c")
                rabbit_user = os.getenv("RABBITMQ_USER", "guest")
                rabbit_pass = os.getenv("RABBITMQ_PASS", "guest")
                rabbit_port = int(os.getenv("RABBITMQ_PORT", "5672"))
                credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
                rabbitmq_connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=rabbit_host, port=rabbit_port, credentials=credentials)
                )
                channel = rabbitmq_connection.channel()
                channel.queue_declare(queue='red_notices_queue', durable=True)
                channel.basic_consume(queue='red_notices_queue', on_message_callback=self._callback, auto_ack=True)
                print("Starting consuming!")
                channel.start_consuming()
                break
            except pika.exceptions.AMQPConnectionError:
                retry_count += 1
                print(f"Connection failed, retrying in 5 seconds... (attempt {retry_count}/{max_retries})")
                time.sleep(5)
            except pika.exceptions.StreamLostError:
                retry_count += 1
                print(f"Stream lost, retrying in 5 seconds... (attempt {retry_count}/{max_retries})")
                time.sleep(5)
            except Exception as e:
                retry_count += 1
                print(f"Unexpected error: {e}, retrying in 5 seconds... (attempt {retry_count}/{max_retries})")
                time.sleep(5)
        if retry_count >= max_retries:
            print("Max retries reached, consumer failed to start")

def callback(ch, method, properties, body):
    consumer = QueueConsumer(PostgresRepository(connection))
    consumer._callback(ch, method, properties, body)


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

pg_cursor = connection.cursor()

repo = PostgresRepository(connection)
repo.ensure_schema()

def start_consumer():
    consumer = QueueConsumer(repo)
    consumer.start()

if __name__ == "__main__":
    start_consumer()