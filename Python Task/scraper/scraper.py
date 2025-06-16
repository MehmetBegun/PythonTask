import os
import time
import pika
from bs4 import BeautifulSoup
import glob
import json

class Scraper:
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.rabbitmq_queue = os.getenv("RABBITMQ_QUEUE", "interpol_queue")
        self.scrape_interval = int(os.getenv("SCRAPE_INTERVAL", "60"))
        self.connection = None
        self.channel = None

    def connect_rabbitmq(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.rabbitmq_queue, durable=True)

    def extract_notices_from_html(self, html_path):
        with open(html_path, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            cards = soup.select(".redNoticesList__item.notice_red")
            for card in cards:
                name = card.select_one(".redNoticeItem__labelLink")
                name = name.get_text(separator=" ").replace("\n", " ").strip() if name else "-"
                age = card.select_one(".ageCount")
                age = age.get_text(strip=True) if age else "-"
                nationality = card.select_one(".nationalities")
                nationality = nationality.get_text(strip=True) if nationality else "-"
                yield {"isim": name, "yaş": age, "uyruk": nationality}

    def send_to_queue(self, notice):
        self.channel.basic_publish(
            exchange='',
            routing_key=self.rabbitmq_queue,
            body=json.dumps(notice),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def run(self):
        self.connect_rabbitmq()
        while True:
            for html_file in glob.glob("/data/sayfa_*.html"):
                for notice in self.extract_notices_from_html(html_file):
                    self.send_to_queue(notice)
            print("[Scraper] Veriler kuyruğa gönderildi. Bekleniyor...")
            time.sleep(self.scrape_interval)

if __name__ == "__main__":
    scraper = Scraper()
    scraper.run() 