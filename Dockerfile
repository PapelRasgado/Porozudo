FROM python:3.11.11
RUN apt-get update && apt-get install -y \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./src ./src
COPY resources/ /app/resources/
ADD credenciais_firebase.json requirements.txt .
RUN pip install -r requirements.txt
RUN pip uninstall discord.py py-cord -y
RUN pip install py-cord
CMD ["python", "-m", "src.main"]