FROM python:3.12.2
WORKDIR /app
COPY reqs.txt /app/
RUN pip install -r /app/reqs.txt
RUN apt update && apt install -y postgresql postgresql-contrib dos2unix
COPY consumer_db.py /app/
COPY webapp.py /app/
COPY templates/definition.html /app/templates/
COPY start_app.sh /app/
RUN dos2unix /app/start_app.sh
RUN chmod +x /app/start_app.sh
EXPOSE 5000
CMD ["/bin/bash", "/app/start_app.sh"]