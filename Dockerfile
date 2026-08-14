FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py config.py data_store.py docker_ops.py domain_ops.py challenge_meta.py routes.py ./
COPY views ./views
COPY page_templates ./page_templates
RUN mkdir -p /data
VOLUME /data

ENV ADMIN_PASSWORD=admin123
ENV SECRET_KEY=change-me-in-production

EXPOSE 8000

CMD ["gunicorn", "-w", "1", "--threads", "8", "--timeout", "120", "-b", "0.0.0.0:8000", "app:app"]
