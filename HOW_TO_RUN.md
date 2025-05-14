# How to Run SayadGanj Telegram Bot on Hetzner VPS

This guide provides step-by-step instructions for deploying and running the SayadGanj Telegram Bot on a Hetzner Linux VPS.

## Prerequisites

- A Hetzner VPS with Ubuntu 20.04 or newer
- SSH access to your VPS
- Domain name (optional, but recommended)
- Telegram Bot API credentials (API_ID, API_HASH, BOT_TOKEN)

## 1. Initial Server Setup

### 1.1. Connect to your VPS

```bash
ssh root@your_server_ip

### 1.2. Update the system
```bash
apt update && apt upgrade -y

# 1.3. Create a non-root user (optional but recommended)
```bash
adduser sayadganj
usermod -aG sudo sayadganj

# Switch to the new user:
```bash
su - sayadganj

# ## 2. Install Docker and Docker Compose
```bash
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce

# 2.2. Add your user to the docker group
```bash
sudo usermod -aG docker $USER

# 2.3. Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify the installation:
```bash
docker --version
docker-compose --version

# 3. Clone the Repository
```bash
sudo apt install -y git

```bash
git clone https://github.com/mo4wez/SayadGanj_Telegram_Bot.git
cd SayadGanj_Telegram_Bot

# 4.1. Create the .env file
```bash
nano .env

# Add the following content (replace with your actual values):
```bash
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_admin_id
TAKBAND_QANDEEL=your_channel_id

# 5.1. Build and start the Docker containers
```bash
docker-compose up -d

# 5.2. Check the logs
```bash
docker-compose logs -f

## 6. Managing the Bot
### 6.1. Stop the bot
```bash
docker-compose down

### 6.2. Restart the bot
```bash
docker-compose restart

### 6.3. Update the bot
```bash
git pull
docker-compose down
docker-compose up -d --build

## 8. Backup
### 8.1. Backup the database and configuration files
```bash
mkdir -p ~/backups/$(date +%Y-%m-%d)
cp sayadganj.db ~/backups/$(date +%Y-%m-%d)/
cp .env ~/backups/$(date +%Y-%m-%d)/
cp book_info.json ~/backups/$(date +%Y-%m-%d)/
cp word_of_day_settings.json ~/backups/$(date +%Y-%m-%d)/

## 9. Troubleshooting
### 9.1. Check container status
```bash
docker ps -a

### 9.2. View detailed logs
```bash
docker-compose logs -f --tail=100

### 9.3. Access the container shell
```bash
docker exec -it sayadganj_bot bash
