#!/bin/bash
set -e

# Initialize log directory
mkdir -p /app/logs

# Clear log files
truncate -s 0 /app/logs/*.log

# Start supervisord in the foreground
exec /usr/local/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf