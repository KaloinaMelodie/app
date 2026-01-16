# syntax=docker/dockerfile:1.6
FROM python:3.11-slim
WORKDIR /app
# COPY requirements.txt .
COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
# -> copie le dossier 'app/' (package) et autres fichiers
COPY . .               
# optionnel mais utile
ENV PYTHONPATH=/app    
# Chemins conteneur (stables)
ENV LOCALES_DIR=/data/locales
ENV GCP_TRANSLATE_LOCATION=global
# GOOGLE_APPLICATION_CREDENTIALS -> /run/secrets/gcp_key.json (via compose)
EXPOSE 8000
RUN [ -f app/app/.env ] && mv app/app/.env app/app/.env.example || true
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
# FROM python:3.11-slim
# WORKDIR /app

# # outils de build + headers SASL/Kerberos/LDAP requis par le package Python "sasl"
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential gcc g++ \
#     libsasl2-dev libkrb5-dev libldap2-dev \
#  && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt

# COPY . .
# ENV LOCALES_DIR=/data/locales
# ENV GCP_TRANSLATE_LOCATION=global
# EXPOSE 8000
# CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
