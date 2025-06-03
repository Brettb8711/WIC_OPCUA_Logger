# OPC UA to Postgres UI (PyQt5) - Raspberry Pi 64-bit Docker

This project provides a PyQt5-based GUI for logging OPC UA node values to a Postgres database. It is packaged for easy deployment on a Raspberry Pi (64-bit, ARM64) using Docker.

## Prerequisites
- Raspberry Pi running a 64-bit OS (e.g., Raspberry Pi OS 64-bit)
- Docker installed on your Raspberry Pi
- X11 server running (for GUI display)
- A running Postgres database accessible from the Pi

## Build the Docker Image
Open a terminal in the project directory and run:

```
docker build -t opcua-postgres-gui .
```

## Run the Docker Container
To run the GUI and display it on your Pi's desktop:

```
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix opcua-postgres-gui
```

- This command enables X11 forwarding so the PyQt5 GUI appears on your desktop.
- If you get display errors, ensure your Pi's desktop is running and X11 is enabled.

## Usage
1. The GUI will open. Enter your Postgres connection string in the bottom right.
2. Click "Add New Connection" to add an OPC UA server:
   - Enter a display name, server URL, and refresh rate.
   - Test the connection, load nodes, select nodes to log, and confirm.
3. The main table will show all logged nodes, their values, and timestamps.
4. Use the filter at the top to view nodes from a specific server.

## Notes
- If you want to run headless (no GUI), you must adapt the app to a web or CLI interface.
- For troubleshooting, check Docker logs and ensure your Postgres server is reachable from the Pi.

## Stopping the Container
Press Ctrl+C in the terminal running the container, or use:
```
docker ps
# Find the container ID, then:
docker stop <container_id>
```

---

**Developed for ARM64 Raspberry Pi. For other platforms, adjust the Dockerfile base image accordingly.**
