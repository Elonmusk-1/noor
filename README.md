# Telegram Group Management Bot

A powerful and feature-rich Telegram bot for managing groups with advanced features like AI integration, federation support, and comprehensive moderation tools.

## Features

- 🛡️ Advanced Group Management
- 🤖 AI Integration (using Gemini API)
- 🌐 Federation Support
- 📊 Analytics and Statistics
- ⚡ Anti-Spam & Anti-Flood Protection
- 📝 Notes and Rules Management
- 🎮 Karma System
- 🔄 Backup and Restore
- 🌍 Multi-language Support
- 📈 Chat Statistics

## Prerequisites

Before deploying, ensure you have:

- Python 3.8 or higher
- PostgreSQL database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Gemini API Key (for AI features)
- Linux server with root access

## Step-by-Step Deployment Guide

### 1. System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib git nginx

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Database Setup

```bash
# Switch to PostgreSQL user
sudo -i -u postgres

# Create database and user
psql -c "CREATE DATABASE group_manager;"
psql -c "CREATE USER botuser WITH PASSWORD 'your_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE group_manager TO botuser;"
psql -c "\q"

# Exit postgres user
exit
```

### 3. Bot Setup

```bash
# Create directory for the bot
mkdir -p /opt/telegram_bot
cd /opt/telegram_bot

# Clone the repository
git clone https://github.com/ukwarjun/noor.git .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Create .env file
nano .env
```

Add the following content (replace with your values):
```env
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
OWNER_ID=your_telegram_id
SUDO_USERS=id1,id2,id3
DB_HOST=localhost
DB_PORT=5432
DB_NAME=group_manager
DB_USER=botuser
DB_PASSWORD=your_password
LOG_CHANNEL=your_log_channel_id
SUPPORT_CHAT=your_support_chat
GEMINI_API_KEY=your_gemini_api_key
```

### 5. Systemd Service Setup

```bash
# Create systemd service file
sudo nano /etc/systemd/system/telegram-bot.service
```

Add the following content:
```ini
[Unit]
Description=Telegram Group Management Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/opt/telegram_bot
Environment=PATH=/opt/telegram_bot/venv/bin
ExecStart=/opt/telegram_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6. Start the Bot

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start the bot
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
```

### 7. Logging Setup

```bash
# Create logs directory
mkdir -p /opt/telegram_bot/logs
chmod 755 /opt/telegram_bot/logs
```

### 8. Nginx Setup (Optional, for webhook)

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/telegram-bot
```

Add the following content:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Maintenance

### Updating the Bot

```bash
cd /opt/telegram_bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

### Viewing Logs

```bash
# View bot logs
sudo journalctl -u telegram-bot -f

# View application logs
tail -f /opt/telegram_bot/logs/bot.log
```

### Backup Database

```bash
# Create backup
pg_dump -U botuser group_manager > backup.sql

# Restore backup
psql -U botuser group_manager < backup.sql
```

## Troubleshooting

1. **Bot not starting**
   - Check logs: `sudo journalctl -u telegram-bot -f`
   - Verify .env file configuration
   - Ensure database is running: `sudo systemctl status postgresql`

2. **Database connection issues**
   - Verify PostgreSQL is running
   - Check database credentials in .env
   - Ensure database user has proper permissions

3. **Permission issues**
   - Check file permissions: `ls -la /opt/telegram_bot`
   - Ensure correct user owns the files: `sudo chown -R your_username:your_username /opt/telegram_bot`

## Security Notes

1. Keep your .env file secure and never commit it to Git
2. Regularly update your system and Python packages
3. Use strong passwords for database and API keys
4. Enable firewall and configure it properly
5. Regularly backup your database

## Support

For support, join our [Support Chat](https://t.me/your_support_chat) or open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 