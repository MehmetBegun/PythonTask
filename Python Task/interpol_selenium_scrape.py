'''
Interpol Red Notice - Selenium Scraper

KULLANIM:
1. pip install selenium pandas
2. https://chromedriver.chromium.org/downloads adresinden ChromeDriver indir, PATH'e ekle (veya script ile aynı klasöre koy)
3. python interpol_selenium_scrape.py

Script, Interpol Red Notices sayfasında ülke ve cinsiyet filtrelerini otomatik olarak gezip, mümkün olan en fazla Red Notice kaydını toplar ve interpol_scraped.csv dosyasına kaydeder.
'''

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
import traceback

URL = "https://www.interpol.int/en/How-we-work/Notices/View-Red-Notices"

# --- Selenium ayarları ---
options = Options()
# options.add_argument("--headless")  # Headless mod KAPALI
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

CHROMEDRIVER_PATH = "chromedriver.exe"  # Dosya script ile aynı klasördeyse
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
driver.get(URL)
driver.maximize_window()

print("Kod başladı")
try:
    time.sleep(30)
    try:
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("page_source.html dosyası kaydedildi.")
    except Exception as e:
        print(f"page_source.html kaydedilemedi: {e}")
        traceback.print_exc()
except Exception as e:
    print(f"Bekleme veya scraping sırasında hata oluştu: {e}")
    traceback.print_exc()

print("Kod bitti")

# --- GEREKSİZ SELECT VE COUNTRY_SELECT KODLARI TAMAMEN SİLİYORUM ---
# Kodun başı ve sonundaki printler, manuel ülke listesi ve input'a yazma işlemleri kalacak.

countries = ["TURKEY", "FRANCE", "GERMANY"]  # Buraya istediğin ülke isimlerini ekle

for country in countries:
    try:
        input_elem = driver.find_element(By.ID, "nationality")
        input_elem.clear()
        input_elem.send_keys(country)
        print(f"{country} için ülke input'una değer yazıldı.")
        # Burada arama butonuna tıklama ve scraping işlemlerini ekleyebilirsin
        # Örneğin:
        # search_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        # search_btn.click()
        # time.sleep(2)  # Sonuçların yüklenmesini bekle
    except Exception as e:
        print(f"{country} için input'a yazılamadı: {e}")
        traceback.print_exc()

# --- Cinsiyetler ---
genders = ["M", "F", "U"]  # Male, Female, Unknown

all_data = []
visited = set()

for country in countries:
    for gender in genders:
        # Filtreleri uygula
        country_select = Select(driver.find_element(By.ID, "nationality"))
        country_select.select_by_value(country)
        gender_select = Select(driver.find_element(By.ID, "sexId"))
        gender_select.select_by_value(gender)
        # Ara butonuna tıkla
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        # Sayfa sayısını bul
        try:
            page_count = len(driver.find_elements(By.CSS_SELECTOR, ".pagination__item:not(.pagination__item--next):not(.pagination__item--prev)"))
            if page_count == 0:
                page_count = 1
        except Exception:
            page_count = 1
        for page in range(1, page_count + 1):
            time.sleep(1)
            # Kayıtları çek
            cards = driver.find_elements(By.CSS_SELECTOR, ".redNoticesList__item.notice_red")
            for card in cards:
                try:
                    name = card.find_element(By.CSS_SELECTOR, ".redNoticeItem__labelLink").text.strip()
                    forename = card.find_element(By.CSS_SELECTOR, ".redNoticeItem__forename").text.strip()
                    dob = card.find_element(By.CSS_SELECTOR, ".redNoticeItem__dob").text.strip()
                    nationality = card.find_element(By.CSS_SELECTOR, ".redNoticeItem__nationality").text.strip()
                    entity_id = card.get_attribute("data-entity-id")
                    thumbnail = card.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                    if entity_id and entity_id not in visited:
                        all_data.append({
                            "entity_id": entity_id,
                            "name": name,
                            "forename": forename,
                            "dob": dob,
                            "nationality": nationality,
                            "gender": gender,
                            "country": country,
                            "thumbnail": thumbnail
                        })
                        visited.add(entity_id)
                except Exception:
                    continue
            # Sonraki sayfa varsa tıkla
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, ".pagination__item--next:not(.pagination__item--disabled)")
                next_btn.click()
                time.sleep(1)
            except NoSuchElementException:
                break
            except ElementClickInterceptedException:
                break
        # Filtreleri sıfırla
        driver.get(URL)
        time.sleep(2)

# Sonuçları kaydet
if all_data:
    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset=["entity_id"], inplace=True)
    df.to_csv("interpol_scraped.csv", index=False)
    print(f"Toplam {len(df)} benzersiz kayıt kaydedildi: interpol_scraped.csv")
else:
    print("Hiç veri bulunamadı.")

driver.quit() 