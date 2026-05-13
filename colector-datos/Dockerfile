FROM python:3.9-slim

# Deshabilitar buffer para que los logs aparezcan en tiempo real
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]