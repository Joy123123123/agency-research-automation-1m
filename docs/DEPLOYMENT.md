# Deployment Guide — Agency Research Automation

## Local Development

```bash
git clone https://github.com/Joy123123123/agency-research-automation-1m.git
cd agency-research-automation-1m
bash scripts/setup.sh
python scripts/run_research.py --niche restaurant --location Dhaka
```

## Production Deployment (VPS/Server)

### Requirements
- Ubuntu 22.04 LTS
- Python 3.10+
- 2GB+ RAM
- Stable internet connection

### Deploy with systemd

```bash
# 1. Clone repo
git clone https://github.com/Joy123123123/agency-research-automation-1m.git /opt/agency-automation

# 2. Setup
cd /opt/agency-automation
bash scripts/setup.sh

# 3. Create systemd service
sudo nano /etc/systemd/system/agency-automation.service
```

```ini
[Unit]
Description=Agency Research Automation Scheduler
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/agency-automation
Environment=PATH=/opt/agency-automation/venv/bin
ExecStart=/opt/agency-automation/venv/bin/python scripts/scheduler.py --start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 4. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable agency-automation
sudo systemctl start agency-automation
sudo systemctl status agency-automation
```

## Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "scripts/scheduler.py", "--start"]
```

```bash
docker build -t agency-automation .
docker run -d --env-file config/api_keys.env agency-automation
```

## Environment Variables

Set these in your production environment or `config/api_keys.env`:

```
OPENAI_API_KEY=...
SENDGRID_API_KEY=...
AIRTABLE_API_KEY=...
GOOGLE_API_KEY=...
APP_ENV=production
LOG_LEVEL=WARNING
EMAIL_DAILY_LIMIT=200
MAX_LEADS_PER_DAY=500
```
