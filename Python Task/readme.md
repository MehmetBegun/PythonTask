# Interpol Red Notice Mikroservis Uygulaması

## Proje Açıklaması
Bu proje, Interpol tarafından yayınlanan kırmızı bülten (Red Notice) verilerini mikroservis mimarisiyle işler. Veriler HTML dosyalarından çekilir, RabbitMQ ile kuyruğa aktarılır, PostgreSQL veritabanına kaydedilir ve Streamlit tabanlı web arayüzünde gösterilir. Tüm yapı Docker Compose ile çoklu container olarak ayağa kalkar.

## Mimari
- **scraper:** HTML dosyalarını okuyup RabbitMQ kuyruğuna veri gönderir.
- **web:** RabbitMQ kuyruğunu dinler, gelen verileri PostgreSQL veritabanına kaydeder ve Streamlit ile web arayüzünde gösterir.
- **rabbitmq:** Mesaj kuyruğu sistemi.
- **postgres:** Kalıcı ve büyük ölçekli veritabanı.

## Özellikler
- OOP (Nesne Tabanlı Programlama) ile yazılmıştır.
- Docker ve docker-compose ile tam izole ve taşınabilir.
- RabbitMQ ile mikroservisler arası iletişim.
- PostgreSQL ile büyük ölçekli veri saklama.
- Web arayüzünde filtreleme, CSV/PDF indirme, otomatik güncelleme.
- Güncellenen kayıtlar için alarm (kırmızı satır).
- Tüm ayarlar environment variable ile yönetilir.
- Testler ve dökümantasyon eksiksizdir.

## Kurulum
1. **Docker Desktop** yüklü olmalı.
2. Proje klasöründe terminal açın:
   ```bash
   docker compose up --build
   ```
3. Web arayüzü: [http://localhost:8501](http://localhost:8501)
4. RabbitMQ yönetim paneli: [http://localhost:15672](http://localhost:15672) (guest/guest)
5. PostgreSQL: [localhost:5432](localhost:5432) (interpol/interpol_user/interpol_pass)

## Testler
- Testleri çalıştırmak için:
  ```bash
  pytest test_interpol.py
  ```
- Testler şunları kapsar:
  - HTML'den veri ayıklama
  - RabbitMQ kuyruğuna mesaj gönderme (mock)
  - PostgreSQL'e veri ekleme ve güncelleme

## Kullanım
- Web arayüzünde filtreleme, arama, CSV/PDF indirme ve otomatik güncellenen tablo ile verileri görüntüleyebilirsiniz.
- Güncellenen kayıtlar kırmızı renkle vurgulanır.

## PDF Gereksinimleri ile Tam Uyum
- 3+ container (scraper, web, rabbitmq, postgres)
- RabbitMQ ile mikroservis iletişimi
- Büyük ölçekli veritabanı (PostgreSQL)
- OOP ile kodlama
- Docker-compose ile çoklu container
- Otomatik arayüz güncelleme
- Alarm/uyarı sistemi
- Test ve dökümantasyon
- Environment/config ile yönetim

## Notlar
- Interpol sitesinin bot korumaları nedeniyle veriler manuel HTML dosyalarından alınmaktadır.
- Projeyi Github/Gitlab'a yükleyerek versiyon kontrolü sağlayabilirsiniz.
- Gelişmiş mimari için kodlar kolayca genişletilebilir.

## Bund.dev API Entegrasyonu
Projede istenirse Interpol verileri `https://interpol.api.bund.dev/` adresindeki
REST API kullanılarak da çekilebilir. Bunun için `interpol_full_scrape.py`
dosyasındaki `INTERPOL_BASE_URL` ve `INTERPOL_API_KEY` ortam değişkenleri
kullanılır. API anahtarınızı `INTERPOL_API_KEY` olarak tanımlayıp scripti
aşağıdaki gibi çalıştırabilirsiniz:

```bash
INTERPOL_BASE_URL=https://interpol.api.bund.dev \
INTERPOL_API_KEY=<your-key> python interpol_full_scrape.py
```

---

**Not:** Eksik veya geliştirilmesi gereken noktalar README'de ve kodda açıklanmıştır. Daha fazla bilgi için PDF görev dosyasına bakınız. 