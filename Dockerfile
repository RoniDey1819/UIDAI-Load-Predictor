FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for build tools)
# RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
