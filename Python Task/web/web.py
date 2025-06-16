import os
import pika
import psycopg2
import json
import streamlit as st
import threading
import pandas as pd
from streamlit_autorefresh import st_autorefresh

@st.cache_resource
def get_db_connection():
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "interpol")
    pg_user = os.getenv("POSTGRES_USER", "interpol_user")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "interpol_pass")
    conn = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        dbname=pg_db,
        user=pg_user,
        password=pg_pass
    )
    return conn

class WebApp:
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.rabbitmq_queue = os.getenv("RABBITMQ_QUEUE", "interpol_queue")
        self.conn = get_db_connection()
        self.c = self.conn.cursor()
        self.setup_db()
        self.start_rabbitmq_listener()

    def setup_db(self):
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id SERIAL PRIMARY KEY,
            isim TEXT,
            yaş TEXT,
            uyruk TEXT,
            zaman TEXT,
            guncellendi INTEGER DEFAULT 0,
            UNIQUE(isim, yaş, uyruk)
        )
        """
        )
        self.conn.commit()

    def rabbitmq_callback(self, ch, method, properties, body):
        data = json.loads(body)
        try:
            self.c.execute(
                "INSERT INTO notices (isim, yaş, uyruk, zaman, guncellendi) VALUES (%s, %s, %s, NOW(), 0)",
                (data["isim"], data["yaş"], data["uyruk"]),
            )
            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            self.c.execute(
                "UPDATE notices SET zaman = NOW(), guncellendi = 1 WHERE isim = %s AND yaş = %s AND uyruk = %s",
                (data["isim"], data["yaş"], data["uyruk"])
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("DB error:", e)

    def listen_rabbitmq(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
        channel = connection.channel()
        channel.queue_declare(queue=self.rabbitmq_queue, durable=True)
        channel.basic_consume(
            queue=self.rabbitmq_queue,
            on_message_callback=self.rabbitmq_callback,
            auto_ack=True,
        )
        print("[Web] Kuyruk dinleniyor...")
        channel.start_consuming()

    def start_rabbitmq_listener(self):
        t = threading.Thread(target=self.listen_rabbitmq, daemon=True)
        t.start()

    def run_streamlit(self):
        st.title("Interpol Red Notice Listesi")
        st_autorefresh(interval=5000, key="otomatik_yenile")
        df = None
        try:
            df = pd.read_sql_query("SELECT * FROM notices ORDER BY zaman DESC", self.conn)
            # Zaman sütununu UTC'den Türkiye saatine çevir ve sadece tarih+saat olarak göster
            if 'zaman' in df.columns:
                df['zaman'] = pd.to_datetime(df['zaman'], utc=True, errors='coerce').dt.tz_convert('Europe/Istanbul')
                df['zaman'] = df['zaman'].dt.strftime('%d.%m.%Y %H:%M')
        except Exception as e:
            st.write("Veri yüklenemedi:", e)
        if df is not None and not df.empty:
            def highlight_row(row):
                if row['guncellendi'] == 1:
                    return ['background-color: #ffcccc'] * len(row)
                else:
                    return [''] * len(row)
            st.dataframe(df.style.apply(highlight_row, axis=1))
            st.caption("Kırmızı satırlar: Güncellenen kayıtlar/alarm!")
        else:
            st.info("Henüz veri yok.")

if __name__ == "__main__":
    app = WebApp()
    app.run_streamlit() 