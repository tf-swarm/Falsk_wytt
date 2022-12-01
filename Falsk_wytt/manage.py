from qts import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
# 导入需要迁移的数据库模型
from qts.models import *

# 实例化一个app对象
app = create_app()
# 使用migrate绑定app和db   绑定 数据库与app,建立关系
migrate = Migrate(app, db)

# 实例化一个manager对象 让python支持命令行工作
manager = Manager(app)
# 添加迁移脚本的命令到manager中
manager.add_command('db', MigrateCommand)

# python3 manage.py db init  初始化  生成migrations文件夹 只做一次就可以
# python3 manage.py db migrate  创建迁移脚本
# python3 hello.py db upgrade  更新数据库
# python3 manage.py downgrade 回退操作
if __name__ == '__main__':
    manager.run()
