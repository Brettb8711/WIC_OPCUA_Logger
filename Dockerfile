# Dockerfile for Raspberry Pi 64-bit (ARM64) running PyQt5 OPC UA Postgres UI
FROM arm64v8/python:3.11

# Install system dependencies for PyQt5 and PostgreSQL
RUN apt-get update && \
    apt-get install -y python3-pyqt5 libqt5gui5 libqt5widgets5 libqt5core5a libqt5dbus5 libxcb-xinerama0 libpq-dev && \
    apt-get clean

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the display variable for X11 forwarding (for GUI)
ENV DISPLAY=:0

# Run the application
CMD ["python", "opcua_postgres_ui.py"]
