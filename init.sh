#!/bin/bash
set -e

echo "=========================================="
echo "  WaterWeb 灌区管理系统初始化脚本"
echo "=========================================="

cd backend

if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python -m venv venv
fi

source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

echo "安装依赖..."
pip install -r requirements.txt

echo "执行数据库迁移..."
export DJANGO_ENV=development
python manage.py migrate

echo "创建超级用户..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123456',
        real_name='系统管理员',
        role='super_admin',
    )
    print('超级用户创建成功: admin / admin123456')
else:
    print('超级用户已存在')
"

echo "创建基础数据..."
python manage.py shell -c "
from apps.common.models import RegionModel, CommonConfig

if RegionModel.objects.count() == 0:
    main = RegionModel.objects.create(code='MAIN', name='总灌区', region_type='area')
    RegionModel.objects.create(code='ZONE_A', name='东区', region_type='area', parent=main)
    RegionModel.objects.create(code='ZONE_B', name='西区', region_type='area', parent=main)
    RegionModel.objects.create(code='CANAL_01', name='东干渠', region_type='canal', parent=main)
    print('灌区区域创建成功')

if CommonConfig.objects.count() == 0:
    CommonConfig.objects.create(config_type='system', config_key='site_name', config_value='灌区管理系统')
    CommonConfig.objects.create(config_type='system', config_key='page_size', config_value=20)
    CommonConfig.objects.create(config_type='notification', config_key='email_enabled', config_value=False)
    print('基础配置创建成功')

print('初始化完成!')
"

echo ""
echo "启动开发服务器..."
echo "访问: http://localhost:8000/"
echo "API文档: http://localhost:8000/api/docs/"
echo "登录: admin / admin123456"
echo ""
echo "运行: python manage.py runserver 0.0.0.0:8000"
