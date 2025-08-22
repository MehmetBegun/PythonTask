FROM python:3.12-slim
WORKDIR /app
COPY reqs.txt ./
RUN pip install --no-cache-dir -r reqs.txt
COPY scraper.py ./
ENV INTERVAL=300
CMD ["python", "scraper.py"]