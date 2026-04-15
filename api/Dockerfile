FROM python:3.11-slim

WORKDIR /app

# asyncpg bundles its own libpq; uvicorn[standard] wheels are pre-compiled.
# No system packages are required.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
