import streamlit as st
import pandas as pd
from datetime import datetime
import os
from bs4 import BeautifulSoup

def get_red_notices(pages: int = 8, per_page: int = 20):
    """8 HTML dosyasından (sayfa_1.html - sayfa_8.html) veri ayıklar."""
    notices = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(1, pages + 1):
        fname = f"sayfa_{i}.html"
        if not os.path.exists(fname):
            continue
        with open(fname, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            cards = soup.select(".redNoticesList__item.notice_red")
            for card in cards:
                name = card.select_one(".redNoticeItem__labelLink")
                name = name.get_text(separator=" ").replace("\n", " ").strip() if name else "-"
                age = card.select_one(".ageCount")
                age = age.text.strip() if age else "-"
                nationality = card.select_one(".nationalities")
                nationality = nationality.text.strip() if nationality else "-"
                notices.append({
                    "İsim": name,
                    "Yaş": age,
                    "Uyruk": nationality,
                    "Veri Çekilme Zamanı": now
                })
    return notices

def main():
    st.set_page_config(page_title="Interpol Kırmızı Bülten", layout="wide")
    
    st.title("Interpol Kırmızı Bülten")
    st.write("Bu uygulama, Interpol'ün Kırmızı Bülten listesindeki aranan kişilerin bilgilerini gösterir.")
    
    # Filtreleme seçenekleri
    st.sidebar.header("Filtreleme Seçenekleri")
    
    # Arama filtresi
    search_query = st.sidebar.text_input("Arama yapın:", "")
    
    # Filtreleme türü
    filter_type = st.sidebar.selectbox(
        "Filtreleme türü:",
        ["Tümü", "İsim", "Yaş", "Uyruk"]
    )
    
    # Verileri session state'de sakla
    if 'notices' not in st.session_state:
        st.session_state.notices = None
    
    if st.button("Verileri Güncelle"):
        with st.spinner("Veriler yükleniyor..."):
            st.session_state.notices = get_red_notices()
    
    if st.session_state.notices:
        # DataFrame oluştur ve index'i 1'den başlat
        df = pd.DataFrame(st.session_state.notices)
        df.index = range(1, len(df) + 1)
        df.index.name = "No"
        
        # Arama filtresi uygula
        if search_query:
            if filter_type == "Tümü":
                mask = (
                    df['İsim'].str.contains(search_query, case=False, na=False) |
                    df['Yaş'].str.contains(search_query, case=False, na=False) |
                    df['Uyruk'].str.contains(search_query, case=False, na=False)
                )
            elif filter_type == "İsim":
                mask = df['İsim'].str.contains(search_query, case=False, na=False)
            elif filter_type == "Yaş":
                mask = df['Yaş'].str.contains(search_query, case=False, na=False)
            elif filter_type == "Uyruk":
                mask = df['Uyruk'].str.contains(search_query, case=False, na=False)
            
            df = df[mask]
        
        # Tüm verileri tablo olarak göster
        st.subheader("Tüm Veriler")
        st.dataframe(df)
    else:
        st.warning("Verileri görmek için 'Verileri Güncelle' butonuna tıklayın.")

if __name__ == "__main__":
    main() 