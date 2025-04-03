FROM python:3.8-alpine
WORKDIR /app
COPY techtrends/ /app
EXPOSE 3111
RUN pip install --no-cache-dir -r requirements.txt && \
    python init_db.py
CMD ["python", "app.py"]
