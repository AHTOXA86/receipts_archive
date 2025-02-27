FROM python:3.12-slim

WORKDIR /app

# Copy the application code
COPY app/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN export PYTHONPATH=/app:$PYTHONPATH

WORKDIR /
# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]