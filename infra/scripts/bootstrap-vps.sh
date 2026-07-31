#!/usr/bin/env bash
# Первичная настройка сервера A (Debian 12). Идемпотентен, запускать от root.
#
# ИСПОЛЬЗОВАНИЕ:
#   bash bootstrap-vps.sh "ssh-ed25519 AAAA... github-actions"
#
# Публичный ключ деплоя передаётся аргументом и ставится ДО закрытия
# парольного входа. Без него скрипт не станет отключать пароли — иначе
# сервер закрывается раньше, чем в него удаётся положить ключ.
set -euo pipefail

DEPLOY_USER=deploy
DEPLOY_PUBKEY="${1:-}"

# Без этих переменных apt пытается открыть диалог debconf, не может
# (нет tty при запуске через ssh) и виснет намертво.
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1
APT_OPTS=(-y -qq -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)

apt-get update -qq
apt-get install "${APT_OPTS[@]}" ca-certificates curl gnupg ufw fail2ban rsync

# --- swap 2 ГБ: страховка от OOM-killer при rolling deploy ---
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
sysctl -w vm.swappiness=10
grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf

# --- Docker из официального репозитория ---
if ! command -v docker >/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install "${APT_OPTS[@]}" docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# --- ротация логов на уровне демона: 60 ГБ диска не должны уйти в логи ---
cat > /etc/docker/daemon.json <<'JSON'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "live-restore": true
}
JSON
systemctl restart docker

# --- пользователь деплоя ---
id -u "$DEPLOY_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash "$DEPLOY_USER"
usermod -aG docker "$DEPLOY_USER"
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" /opt/sorxill

# --- ключ деплоя ставим ДО ужесточения SSH ---
if [[ -n "$DEPLOY_PUBKEY" ]]; then
  install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
  AUTH="/home/$DEPLOY_USER/.ssh/authorized_keys"
  touch "$AUTH"
  grep -qxF "$DEPLOY_PUBKEY" "$AUTH" || echo "$DEPLOY_PUBKEY" >> "$AUTH"
  chown "$DEPLOY_USER:$DEPLOY_USER" "$AUTH"
  chmod 600 "$AUTH"
  echo "✓ ключ деплоя установлен для $DEPLOY_USER"
fi

# --- сеть и SSH ---
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80,443/tcp
ufw --force enable

# Закрываем парольный вход ТОЛЬКО если есть чем зайти после этого.
if [[ -s "/home/$DEPLOY_USER/.ssh/authorized_keys" ]]; then
  sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
  sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
  systemctl reload ssh
  echo "✓ SSH: только по ключам"
else
  echo "⚠️  Ключ деплоя не передан — парольный вход НЕ отключён."
  echo "   Иначе сервер закрылся бы раньше, чем в него удалось положить ключ."
  echo "   Положите ключ и перезапустите скрипт с аргументом."
fi

systemctl enable --now fail2ban

# Автообновления безопасности включаем конфигом, а не dpkg-reconfigure:
# последний требует управляющий терминал и через ssh зависает.
apt-get install "${APT_OPTS[@]}" unattended-upgrades
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
CONF
systemctl enable --now unattended-upgrades 2>/dev/null || true

echo
echo "✓ сервер готов."
if [[ -n "$DEPLOY_PUBKEY" ]]; then
  echo "  Проверьте с локальной машины: ssh -i ~/.ssh/sorxill_deploy $DEPLOY_USER@<ip> docker ps"
fi
