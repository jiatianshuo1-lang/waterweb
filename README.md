# 灌区管理系统 (WaterWeb)

一个功能完整的智慧灌区管理系统，包含前端Vue3和后端Django REST Framework。

## 📋 功能模块

| 模块 | 说明 |
|------|------|
| 🔍 巡检与工单管理 | 巡检计划、执行、工单创建和全流程管理 |
| 💧 灌区量测水管理 | 测站管理、实时数据采集、水量告警 |
| 🎯 智慧灌排 | 灌溉设备远程控制、智能灌溉计划 |
| 🌊 均衡水资源分配 | 水源管理、分配方案、跨区域调水 |
| 💰 农业水价改革管理 | 水价政策、用水户、水费账单 |
| 📊 灌区日常管理信息化 | 通知公告、会议、固定资产、文档 |
| 🌱 墒情气象监测 | 土壤墒情、气象数据、智能预报 |
| 🤖 AI智能助手 | 前端悬浮弹窗，对接大模型问答 |

## 🏗️ 技术架构

### 后端
- **Django 5.x** + **Django REST Framework**
- **PostgreSQL** 主数据库，**Redis** 缓存/会话
- **JWT** 认证，支持 Token 黑名单
- 按业务域拆分 9 个 Django App
- 统一异常处理、日志按模块拆分

### 前端
- **Vue 3** + **Vite 5** + **Pinia**
- **Element Plus** UI 组件库
- **ECharts** 数据可视化
- 响应式布局，支持权限控制
- AI助手以悬浮弹窗形式集成

### 部署
- **Docker Compose** 一键部署
- **Gunicorn** + **WhiteNoise** 静态文件
- **Nginx** 反向代理、静态服务
- 环境变量配置，支持开发/生产环境切换

## 📁 项目结构

```
waterweb/
├── backend/                        # Django 后端
│   ├── config/                     # Django 项目配置
│   │   ├── settings/               # 分环境配置 (base/development/production/testing)
│   │   ├── urls.py                 # 主路由
│   │   ├── wsgi.py / asgi.py
│   ├── apps/                       # 业务应用
│   │   ├── users/                  # 用户与权限
│   │   ├── common/                 # 公共基础设施
│   │   ├── inspection/             # 巡检+工单管理
│   │   ├── water_measurement/      # 灌区量测水管理
│   │   ├── smart_irrigation/       # 智慧灌排
│   │   ├── water_allocation/       # 均衡水资源分配
│   │   ├── water_price/            # 农业水价改革管理
│   │   ├── daily_management/       # 灌区日常管理
│   │   ├── soil_weather/           # 墒情气象监测
│   │   └── ai_assistant/           # AI智能助手
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/                       # Vue3 前端
│   ├── src/
│   │   ├── api/                    # API 请求封装
│   │   ├── components/             # 公共组件（含AI助手弹窗）
│   │   ├── layouts/                # 主布局
│   │   ├── router/                 # 路由配置
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── utils/                  # 工具函数
│   │   ├── views/                  # 页面视图（按模块组织）
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── init.sh / init.bat              # 快速初始化脚本
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐生产部署）

```bash
# 1. 复制环境变量配置
cp .env.example .env
# 编辑 .env 配置生产环境参数

# 2. 启动所有服务
docker compose up -d --build

# 3. 创建超级用户（首次部署）
docker compose exec backend python manage.py createsuperuser

# 4. 访问系统
# 前端: http://localhost
# 后端: http://localhost:8000
# API文档: http://localhost/api/docs/
```

### 方式二：本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
# 数据库配置: 开发模式默认使用 SQLite，生产使用 PostgreSQL
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000

# 前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

或使用一键脚本：
- Windows: `init.bat`
- Linux/Mac: `bash init.sh`

默认登录: `admin` / `admin123456`

## ⚙️ 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DJANGO_ENV` | 运行环境 (development/production) | development |
| `DJANGO_SECRET_KEY` | Django密钥，生产必改 | change-me |
| `DB_NAME` | 数据库名称 | waterweb |
| `DB_USER` | 数据库用户 | postgres |
| `DB_PASSWORD` | 数据库密码 | postgres |
| `DB_HOST` | 数据库主机 | localhost |
| `REDIS_URL` | Redis连接 | redis://localhost:6379/1 |
| `CORS_ALLOWED_ORIGINS` | 允许的跨域源 | http://localhost:5173 |
| `ALLOWED_HOSTS` | 允许的主机 | * |

## 🤖 AI智能助手

AI助手以**悬浮弹窗**形式集成在前端右下角。配置方式：

1. 登录后台: http://localhost:8000/admin/
2. 添加 AI助手配置，支持的服务商：
   - OpenAI / Azure OpenAI
   - 阿里云百炼 (qwen)
   - 豆包 / DeepSeek
   - Ollama (本地部署)
3. 支持知识库（FAQ、文档、操作流程），AI回答时自动检索相关内容
4. 会话持久化，支持历史记录查看

## 🔐 权限体系

角色从高到低：
- `super_admin` 超级管理员（系统全部权限）
- `admin` 系统管理员（用户管理、系统配置）
- `manager` 灌区负责人（本区域数据管理）
- `inspector` 巡检员（巡检任务执行）
- `worker` 运维人员（工单处理）
- `viewer` 只读用户（仅查看）

## 📝 API概览

所有API统一响应格式：
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 路径前缀 | 模块 |
|----------|------|
| `/api/v1/auth/` | 登录认证 |
| `/api/v1/users/` | 用户管理 |
| `/api/v1/inspection/` | 巡检与工单 |
| `/api/v1/water-measurement/` | 量测水 |
| `/api/v1/smart-irrigation/` | 智慧灌排 |
| `/api/v1/water-allocation/` | 水资源分配 |
| `/api/v1/water-price/` | 水价管理 |
| `/api/v1/daily/` | 日常管理 |
| `/api/v1/soil-weather/` | 墒情气象 |
| `/api/v1/ai/` | AI助手 |

完整API文档: `/api/docs/` (Swagger UI)

## 📊 日志

日志按业务模块拆分，位于 `backend/logs/`：
- `general.log` 通用日志
- `inspection.log` 巡检工单
- `water.log` 水量相关
- `ai_assistant.log` AI助手
- `error.log` 错误日志

## 📄 License

MIT
