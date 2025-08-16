# Use the official Ubuntu image as the base image
FROM python:3.12.9-slim-bookworm

LABEL org.opencontainers.image.source=https://github.com/KD-MM2/opensubtitles-legacy-api
LABEL org.opencontainers.image.description="A FastAPI-based proxy service that provides backward compatibility with the old OpenSubtitles REST API while using the new OpenSubtitles JSON API."
LABEL org.opencontainers.image.licenses=MIT

# Set environment variables to avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

ARG VERSION

# Set up a working directory
WORKDIR /app
RUN mkdir -p /app/logs

# Copy application files
COPY opensubtitles_legacy_api-${VERSION}-py3-none-any.whl ./

# Install Python dependencies
RUN pip install --no-cache-dir opensubtitles_legacy_api-${VERSION}-py3-none-any.whl

# Clean up
RUN rm /app/opensubtitles_legacy_api-${VERSION}-py3-none-any.whl

# Copy the startup script and supervisor configuration
COPY start.sh /app/start.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make the startup script executable
RUN chmod +x /app/start.sh

# Expose the port for the FastAPI server
EXPOSE 8000

# Run supervisord
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
