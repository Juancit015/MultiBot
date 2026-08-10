FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid 1001 --create-home --shell /usr/sbin/nologin app && \
    mkdir -p /app/downloads && \
    chown -R app:app /app/downloads

USER app

ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python3", "multibot.py"]
