#!/bin/bash
# ============================================================
# WaterWeb 日常更新脚本
# 拉取最新代码并重建容器（数据卷保留）
# ============================================================
set -e

DEPLOY_DIR="${DEPLOY_DIR:-$HOME/waterweb}"
BRANCH="${BRANCH:-main}"

cd "$DEPLOY_DIR" || { echo "目录不存在: $DEPLOY_DIR"; exit 1; }

USE_DC="docker compose"
docker compose version &> /dev/null || USE_DC="docker-compose"

echo "[1/2] 拉取最新代码 ($BRANCH)..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "[2/2] 重建并启动容器（保留数据库/媒体数据）..."
$USE_DC up -d --build

echo ""
echo "更新完成。查看日志: $USE_DC logs -f"
