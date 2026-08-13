@echo off
chcp 65001 >nul
echo ==========================================
echo   WaterWeb 灌区管理系统初始化脚本
echo ==========================================

cd backend

if not exist venv (
    echo 创建 Python 虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo 安装依赖...
pip install -r requirements.txt

set DJANGO_ENV=development

echo 执行数据库迁移...
python manage.py migrate

echo 创建超级用户...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(username='admin', email='admin@example.com', password='admin123456', real_name='系统管理员', role='super_admin') if not User.objects.filter(username='admin').exists() else None; print('超级用户: admin / admin123456')"

echo 创建基础数据...
python manage.py shell -c "from apps.common.models import RegionModel, CommonConfig; RegionModel.objects.create(code='MAIN', name='总灌区', region_type='area') if RegionModel.objects.count() == 0 else None; print('初始化完成!')"

echo.
echo ==========================================
echo   初始化完成!
echo ==========================================
echo 启动服务器: python manage.py runserver 0.0.0.0:8000
echo 访问: http://localhost:8000/
echo 登录: admin / admin123456
echo ==========================================

pause
