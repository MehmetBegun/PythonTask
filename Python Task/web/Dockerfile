FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY web.py ./
CMD ["streamlit", "run", "web.py", "--server.address=0.0.0.0"] 