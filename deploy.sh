#!/bin/bash
# KADER DZ Bot — one-shot deploy script for Ubuntu/Debian VDS
# Run as root: bash deploy.sh

set -e

BOT_DIR="/opt/kaderdz-bot"
SERVICE="kaderdz-bot"

echo "==> Updating packages and installing Python..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git

echo "==> Creating system user 'botuser'..."
id -u botuser &>/dev/null || useradd --system --no-create-home --shell /bin/false botuser

echo "==> Copying bot files to $BOT_DIR..."
mkdir -p "$BOT_DIR"
cp -r . "$BOT_DIR/"
chown -R botuser:botuser "$BOT_DIR"

echo "==> Creating Python virtual environment..."
python3 -m venv "$BOT_DIR/.venv"
"$BOT_DIR/.venv/bin/pip" install --quiet --timeout 60 -r "$BOT_DIR/requirements.txt"

echo "==> Installing systemd service..."
cp "$BOT_DIR/kaderdz-bot.service" /etc/systemd/system/kaderdz-bot.service
systemctl daemon-reload
systemctl enable "$SERVICE"

# Create .env if it doesn't exist yet
if [ ! -f "$BOT_DIR/.env" ]; then
    echo ""
    echo "⚠️  No .env file found. Creating one now — fill in your values:"
    cp "$BOT_DIR/.env.example" "$BOT_DIR/.env"
    chown botuser:botuser "$BOT_DIR/.env"
    chmod 600 "$BOT_DIR/.env"
    echo "   Edit $BOT_DIR/.env then run:  systemctl start $SERVICE"
    echo ""
else
    echo "==> Starting bot service..."
    systemctl restart "$SERVICE"
    sleep 2
    systemctl status "$SERVICE" --no-pager
fi

echo ""
echo "Done! Useful commands:"
echo "  View logs:    journalctl -u $SERVICE -f"
echo "  Stop bot:     systemctl stop $SERVICE"
echo "  Restart bot:  systemctl restart $SERVICE"
echo "  Status:       systemctl status $SERVICE"
