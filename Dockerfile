# Dockerfile for Hugging Face Spaces (Docker SDK) — also works on any
# container host. The bot serves the mini app on $PORT (Spaces expects 7860).
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=7860
EXPOSE 7860

CMD ["python", "bot.py"]
