#!/bin/bash
# ============================================================
# WaterWeb 首次部署脚本
# 1. 从 GitHub 拉取代码
# 2. 创建 .env（从 .env.production 模板复制）
# 3. docker compose up -d --build
# ============================================================
set -e

GIT_REPO="${GIT_REPO:-https://github.com/YOUR_USERNAME/waterweb.git}"
DEPLOY_DIR="${DEPLOY_DIR:-$HOME/waterweb}"
BRANCH="${BRANCH:-main}"

echo "====== WaterWeb 部署 ======"
echo "仓库: $GIT_REPO"
echo "目录: $DEPLOY_DIR"
echo "分支: $BRANCH"

if ! command -v docker &> /dev/null; then
    echo "错误：未检测到 Docker，请先执行 bash server_setup.sh"
    exit 1
fi

if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
    echo "错误：未检测到 docker compose 插件"
    exit 1
fi

USE_DC="docker compose"
docker compose version &> /dev/null || USE_DC="docker-compose"

if [ ! -d "$DEPLOY_DIR/.git" ]; then
    echo "[1/3] 克隆仓库..."
    git clone -b "$BRANCH" "$GIT_REPO" "$DEPLOY_DIR"
else
    echo "[1/3] 已存在仓库，拉取最新代码..."
    cd "$DEPLOY_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
fi

cd "$DEPLOY_DIR"

if [ ! -f ".env" ]; then
    echo "[2/3] 创建 .env 配置文件..."
    cp .env.production .env
    echo ""
    echo "============================================"
    echo "  ⚠️  请编辑 .env 文件修改生产配置！"
    echo "============================================"
    echo "  nano $DEPLOY_DIR/.env"
    echo "  必须修改的项："
    echo "    DJANGO_SECRET_KEY"
    echo "    DB_PASSWORD"
    echo "    ADMIN_PASSWORD"
    echo "    ALLOWED_HOSTS / CORS_ALLOWED_ORIGINS"
    echo "============================================"
    echo ""
    read -p "配置好 .env 后按回车继续（或 Ctrl+C 退出手动配置）..."
else
    echo "[2/3] .env 已存在，跳过"
fi

echo "[3/3] 启动服务..."
$USE_DC up -d --build

echo ""
echo "====== 部署完成 ======"
echo "前端: http://$(hostname -I | awk '{print $1}')"
echo "API : http://$(hostname -I | awk '{print $1}')/api/docs/"
echo "管理: http://$(hostname -I | awk '{print $1}')/admin/"
echo ""
echo "查看日志: $USE_DC logs -f"
echo "停止服务: $USE_DC down"
