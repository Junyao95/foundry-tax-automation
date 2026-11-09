# Foundry hosted agents expect the process to listen on port 8088.
# This image is built remotely by azd (`dependencyResolution: remote_build`).
FROM python:3.13-slim

ENV PYTHONNOUSERSITE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/user_agent

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8088

CMD ["python", "main.py"]
