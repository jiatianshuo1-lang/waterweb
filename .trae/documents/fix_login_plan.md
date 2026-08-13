# 修复登录 500 错误

## 根因
后端日志 `relation "users_user" does not exist` → PostgreSQL 里缺少 users 表。
原因：docker-compose.yml 的 backend 服务没有等 postgres healthy 就启动，entrypoint 的 `migrate` 在 postgres 还没 ready 时跑失败了。

## 服务器上执行（共 4 步）

### Step 1. 修复 docker-compose.yml（加上 depends_on healthy 条件）
```bash
cd ~/waterweb
# 备份
cp docker-compose.yml docker-compose.yml.bak
# 确认当前内容
grep -A3 "backend:" docker-compose.yml
```

### Step 2. 手动清库重建（最干净）
```bash
# 停所有容器 + 删 postgres 数据卷（重来）
docker-compose down
docker volume rm waterweb_postgres_data 2>/dev/null

# 重新启动
docker-compose up -d
```

### Step 3. 确认迁移跑成功
```bash
# 等 postgres healthy
sleep 5
docker-compose exec backend python manage.py migrate --noinput
# 期望看到: Applying users.0001_initial... OK

# 再次验证 health
curl -s http://localhost:8000/api/v1/common/health/
```

### Step 4. 创建 admin + 验证登录
```bash
# 创建 admin（非交互式）
docker-compose exec -T backend python -c "
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.production')
import django; django.setup()
from django.contrib.auth import get_user_model
U=get_user_model()
u,p='admin','admin123456'
U.objects.filter(username=u).exists() or U.objects.create_superuser(u,'admin@example.com',p)
print('OK: admin / admin123456')
"

# 端到端验证（nginx → backend）
curl -s http://localhost/api/v1/auth/login/ \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}'
# 期望: {"code":0,"data":{"access":"eyJ...","refresh":"eyJ..."}}
```

## 本地 docker-compose.yml 也要同步修复
改 backend 服务的 depends_on：
```yaml
  backend:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```
改完 commit push，服务器下次 `git pull && docker-compose up -d` 就能自动生效。

## 验证标准
- `curl login` 返回 JSON 带 access token
- 浏览器 http://公网IP/ 用 admin/admin123456 登录成功
