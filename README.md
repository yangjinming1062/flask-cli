# flask-cli
一个前后端分离的基于flask的API框架
启动服务后通过/api/docs来访问Swagger界面

## 安装项目依赖：
```
pip3 install -r requirements.txt
```

## 数据库初始化：
```
python3 manager.py db init
python3 manager.py db migrate
python3 manager.py db upgrade
```

## 启动API服务器：
```
gunicorn app:app -c gunicorn.conf.py
```

### 查看当前服务进程
```
pstree -ap|grep gunicorn
```

### 重启API服务器：
```
kill -HUP **
```

### 退出API服务器：
```
kill -9 **
```
