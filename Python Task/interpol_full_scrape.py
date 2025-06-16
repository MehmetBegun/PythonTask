import os
import requests
import time
import json

# Base URL optionally overridable to support different endpoints, e.g.
# https://interpol.api.bund.dev
BASE_URL = os.getenv("INTERPOL_BASE_URL", "https://ws-public.interpol.int/notices/v1/red")
API_KEY = os.getenv("INTERPOL_API_KEY")
RESULTS_PER_PAGE = 160  # Sayfa başına maksimum sonuç sayısı

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.interpol.int/",
}

if API_KEY:
    # Custom API endpoints may require an API key for authentication
    headers["x-api-key"] = API_KEY

def extract_red_notice_data(notice):
    """
    Bir kırmızı bülten verisinden (JSON) gerekli bilgileri ayıklar.
    """
    try:
        # Şemaya göre alanları güncelleyebiliriz
        name = notice['name']
        nationalities = notice['nationalities']
        age_min = notice['age_min']
        age_max = notice['age_max']
        return {
            "name": name,
            "nationalities": nationalities,
            "age_min": age_min,
            "age_max": age_max
        }
    except KeyError as e:
        print(f"Eksik anahtar: {e}")
        return None

def get_all_red_notices():
    """
    Interpol API'sinden tüm kırmızı bültenleri çeker.
    """
    page_number = 1
    all_notices = []

    while True:
        params = {"page": page_number, "resultPerPage": RESULTS_PER_PAGE}
        try:
            response = requests.get(BASE_URL, headers=headers, params=params)
            response.raise_for_status()  # Hata durumunda exception yükselt

            data = response.json()

            # Şemaya göre _embedded alanındaki notices'ı alıyoruz
            notices = data['_embedded']['notices']

            if not notices:
                break  # Sayfa boşsa döngüyü sonlandır

            for notice in notices:
                extracted_data = extract_red_notice_data(notice)
                if extracted_data:
                    all_notices.append(extracted_data)

            page_number += 1
            print(f"Sayfa {page_number - 1} çekildi. Toplam {len(all_notices)} kayıt.")
            time.sleep(1)  # API'ye çok sık istek göndermemek için bekleyin

        except requests.exceptions.RequestException as e:
            print(f"İstek hatası: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            break
        except Exception as e:
            print(f"Genel hata: {e}")
            break

    return all_notices

if __name__ == "__main__":
    all_red_notices = get_all_red_notices()
    print(f"Toplam {len(all_red_notices)} kırmızı bülten bulundu.")

    # Verileri bir dosyaya kaydetme (isteğe bağlı)
    with open("red_notices.json", "w", encoding="utf-8") as f:
        json.dump(all_red_notices, f, indent=2, ensure_ascii=False)
    print("Veriler red_notices.json dosyasına kaydedildi.")
