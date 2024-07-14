# Use the official Python image from the Docker Hub
FROM python:3.10-bookworm

COPY ./requirements.txt /app/requirements.txt

# Set the working directory in the container
WORKDIR /app

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./bot.py"]