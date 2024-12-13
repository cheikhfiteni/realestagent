FROM python:3.12-slim

WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# # Create and activate virtual environment
# RUN python3 -m venv /app/venv
# ENV PATH="/app/venv/bin:$PATH"

# Install uv in the virtual environment
RUN pip install uv

COPY requirements.txt .
RUN uv pip sync --system requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]