FROM python:3.11.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY bot/ ./bot/
COPY shared/ ./shared/

RUN pip install --no-cache-dir -r bot/requirements.txt

RUN pip uninstall discord.py py-cord -y
RUN pip install --no-cache-dir py-cord

RUN chmod +x ./bot/docker-entrypoint.sh

ENTRYPOINT ["./bot/docker-entrypoint.sh"]

CMD ["python", "-m", "bot.main"]