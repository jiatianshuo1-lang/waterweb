#!/bin/bash
# ============================================================
# WaterWeb 服务器初始化脚本 (Ubuntu 22.04)
# 作用：安装 Docker + Docker Compose + Git
# 使用：ssh 到服务器后执行  bash server_setup.sh
# ============================================================
set -e

echo "====== WaterWeb 服务器初始化 ======"

if [ "$(uname)" != "Linux" ]; then
    echo "错误：本脚本仅用于 Linux 服务器"
    exit 1
fi

echo "[1/4] 系统更新..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release git ufw

echo "[2/4] 安装 Docker..."
if command -v docker &> /dev/null; then
    echo "  Docker 已安装: $(docker --version)"
else
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "  Docker 安装完成: $(docker --version)"
fi

echo "[3/4] 配置防火墙（仅开放 22/80/443）..."
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable || true
sudo ufw status

echo "[4/4] 启用 Docker 开机自启..."
sudo systemctl enable docker
sudo systemctl start docker

echo ""
echo "====== 初始化完成 ======"
echo "请 退出 SSH 后重新登录 让 docker 用户组生效"
echo "然后执行:  bash deploy.sh"
