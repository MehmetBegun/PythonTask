# Python 3.9 tabanlı resmi imajı kullan
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Gerekli dosyaları kopyala
COPY requirements.txt ./
COPY interpol.py ./
COPY sayfa_1.html ./
COPY sayfa_2.html ./
COPY sayfa_3.html ./
COPY sayfa_4.html ./
COPY sayfa_5.html ./
COPY sayfa_6.html ./
COPY sayfa_7.html ./
COPY sayfa_8.html ./

# Bağımlılıkları yükle
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit'in 8501 portunu aç
EXPOSE 8501

# Uygulamayı başlat
CMD ["streamlit", "run", "interpol.py", "--server.address=0.0.0.0"] 