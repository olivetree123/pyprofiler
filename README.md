# pyprofiler

### 安装
```
pip install pyprofiler
```


### 使用
```python
from pyprofiler import PyProfiler

profiler = PyProfiler(func_name="GetUserInfo", filepath="views/user.py")

@profiler
def GetUserInfo(request):
    pass
```

### Todo
1. 线程安全？(YES)
2. 协程安全？(NO)
3. 如何在多线程框架中使用？比如flask、django
4. 如何在协程框架中使用？比如fastapi、sanic