# Use a lightweight Python image
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y netcat && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY ./app /app
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Install dependencies
RUN pip install -r requirements.txt
# --no-cache-dir
# Expose application port
EXPOSE 5000

# Command to run the app
CMD ["python", "main.py"]
