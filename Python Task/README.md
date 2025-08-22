## 3 Konteynerli Python/Docker Uygulaması

Bu proje, verileri periyodik olarak çekip bir mesaj kuyruğuna (RabbitMQ) yazar; tüketici bir servis bu veriyi veritabanına kaydeder ve Flask tabanlı bir web arayüzünde listeler. Mimari 3 konteynerden oluşur ve `docker-compose` ile çalıştırılır.

### Mimarî genel bakış
- Container A (Scraper/Producer): API’den veriyi belirli aralıklarla çeker, RabbitMQ’ya yollar.
- Container B (Consumer + Web + DB başlatma): RabbitMQ kuyruğunu dinler, veriyi PostgreSQL’e yazar ve Flask ile HTML arayüzde gösterir.
- Container C (Queue): RabbitMQ (yönetim paneli dahildir).

Veri akışı: A → C (RabbitMQ) → B (Consumer → PostgreSQL → Flask web).

### Dizin yapısı
```
ContainerA/
  Dockerfile
  reqs.txt
  scraper.py

ContainerB/
  consumer_db.py
  Dockerfile
  pg_hba.conf
  reqs.txt
  start_app.sh
  templates/
    definition.html
  webapp.py

ContainerC/
  Dockerfile

tests/
  test_scraper_unit.py
  test_consumer_repo_unit.py

docker-compose.yml
README.md
```

### Hızlı başlangıç
Önkoşullar: Docker Desktop (veya Docker Engine) kurulu olmalıdır.

1) .env dosyanızı oluşturun (örnek değerler):
```
INTERVAL=300
RABBITMQ_HOST=container_c
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

DB_HOST=127.0.0.1
DB_NAME=postgres_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
```

2) Derle ve çalıştır:
```
docker compose build
docker compose up -d
```

3) Erişim noktaları:
- Web arayüz: http://localhost:8080
- RabbitMQ Yönetim: http://localhost:15672 (kullanıcı/parola: .env’deki değerler; varsayılan guest/guest)

Not: `ContainerB` içinde PostgreSQL servisleri başlatılır ve tablo otomatik oluşturulur. İlk açılışta birkaç saniye beklemek gerekebilir.

### Ortam değişkenleri
- INTERVAL: Scraper çalıştırma periyodu (saniye) — Container A
- RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS: RabbitMQ bağlantı bilgileri
- DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT: Web uygulaması/consumer için PostgreSQL bağlantısı

Mevcut durumda kodun bazı bölümleri varsayılan değerleri sabit kullanmaktadır (örn. `container_c`, `localhost`). `docker-compose.yml` .env değerlerini iletir; ilerleyen sürümlerde tüm bileşenler bu değişkenleri doğrudan koddan da okuyacak şekilde genişletilecektir.

### Veritabanı
Oluşan tablo: ``
- id SERIAL PRIMARY KEY
- entity_id VARCHAR(128) UNIQUE
- name_surname VARCHAR(200)
- age VARCHAR(100)
- nationality VARCHAR(120)
- updated_at TIMESTAMP DEFAULT NOW()

### Testler
- Host ortamında çalıştırma (Windows/PowerShell):
  - `py -m pip install -q -r ContainerA/reqs.txt`
  - `py -m pip install -q -r ContainerB/reqs.txt`
  - `py -m pip install -q pytest`
  - `py -m pytest -q`

### Performans notu
Şu an ~6100–6500 benzersiz kayıt çekilebilmektedir.

### Geliştirme ipuçları
- Loglar için: `docker compose logs -f container_a` (scraper), `container_b`, `container_c`.

- Servisleri durdurma: `docker compose down`.
