import sys
import time
import threading
from functools import wraps

from cachetools import LRUCache


class Function(object):
    """用于记录函数信息的类，用户通常不需要直接使用这个类，而是通过PyProfiler类来调用。
    """

    def __init__(self, name, filepath, lineno=0, code=None):
        self.name = name
        self.code = code
        self.lineno = lineno
        self.filepath = filepath
    
    def equals(self, func):
        if self.code == func.code:
            return True
        if self.name == func.name and self.filepath == func.filepath:
            if self.lineno == 0 or self.lineno == func.lineno:
                if not self.code:
                    self.code = func.code
                return True
        return False


class LogFile(object):
    """用于记录日志的类，用户通常不需要直接使用这个类，而是通过PyProfiler类来调用。"""
    _instance = None

    def __init__(self, log_path, target_func: Function = None):
        """
        Args:
            log_path (_type_): _description_
            target_func (Function, optional): 需要被分析的函数，如果不传入，则分析所有函数。默认是None。
                                                如果传入，会记录这个函数的每一行代码的执行时间；
                                                如果不传入，只记录函数的调用和返回时间；
        """
        self.log_path = log_path
        self.target_func = target_func
        self.data = LRUCache(maxsize=10000)
        self.functions = LRUCache(maxsize=10000)

    @classmethod
    def init_instance(cls, log_path, target_func: Function = None):
        if not cls._instance:
            cls._instance = cls(log_path, target_func)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            raise ValueError("LogFile instance is not initialized")
        return cls._instance

    def register(self):
        thread_id = threading.current_thread().ident
        self.data[thread_id] = []
        self.functions[thread_id] = {}

    def call_func(self, func: Function):
        thread_id = threading.current_thread().ident
        if thread_id not in self.data:
            return
        t = time.time()
        self.functions[thread_id][func.code] = {"start_time": t}
        line = "\n" if not self.target_func or self.target_func.equals(func) else ""
        line = line + f"{int(t*1000)}  call   [{func.name}] on line:{func.lineno} of {func.filepath}\n"
        self.data[thread_id].append(line)

    def run_line(self, func: Function):
        thread_id = threading.current_thread().ident
        if thread_id not in self.data:
            return
        if self.target_func and self.target_func.equals(func):
            self.data[thread_id].append(
                f"{int(time.time()*1000)}  line   [{func.name}] "
                f"on line:{func.lineno} of {func.filepath}\n"
            )

    def return_func(self, func: Function):
        thread_id = threading.current_thread().ident
        if thread_id not in self.data:
            return
        t = time.time()
        coast_time = t - self.functions[thread_id][func.code]["start_time"]
        self.data[thread_id].append(
            f"{int(t*1000)}  return [{func.name}] on line:{func.lineno} "
            f"of {func.filepath} totally {coast_time*1000} ms coast\n"
        )

    def append(self, content: str):
        thread_id = threading.current_thread().ident
        if thread_id not in self.data:
            return
        self.data[thread_id].append(content)

    def commit(self):
        thread_id = threading.current_thread().ident
        if thread_id not in self.data:
            return
        with threading.Lock():
            with open(self.log_path, "a+") as f:
                f.writelines(self.data.pop(thread_id))
        self.functions.pop(thread_id)

    def clean(self):
        thread_id = threading.current_thread().ident
        if thread_id not in self.data:
            return
        self.data.pop(thread_id)
        self.functions.pop(thread_id)


def trace_calls(frame, event, arg):
    if event == "call":
        func = Function(name=frame.f_code.co_name,
                        filepath=frame.f_code.co_filename,
                        code=frame.f_code.co_code)
        LogFile.get_instance().call_func(func=func)
        return trace_calls

    if event == "line":
        func = Function(name=frame.f_code.co_name,
                        filepath=frame.f_code.co_filename,
                        code=frame.f_code.co_code)
        LogFile.get_instance().run_line(func=func)
        return trace_calls

    if event == "return":
        func = Function(name=frame.f_code.co_name,
                        filepath=frame.f_code.co_filename,
                        code=frame.f_code.co_code)
        LogFile.get_instance().return_func(func=func)
        return trace_calls

    return None


class PyProfiler(object):

    def __init__(self,
                 func_name,
                 filepath,
                 lineno: int = 0,
                 log_path: str = "pyprofiler.txt",
                 min_interval: float = 0):
        """PyProfiler是一个用于Python代码性能分析的装饰器

        Args:
            func_name (str, optional): 需要被分析的函数名；
            filepath (str, optional): 需要被分析的函数所在文件路径，相对路径或绝对路径；
            lineno (int, optional): 需要被分析的函数所在行号。如果函数名在文件中唯一，可以写0，默认是0；
                                    函数名唯一，指的是不和其他函数或类方法同名；
            log_path (str, optional): 日志文件路径，默认是pyprofiler.txt；
            min_interval (float, optional): 日志需要记录的最小时间间隔，单位是毫秒(ms)，默认是0；
        """
        self.func_name = func_name
        self.filepath = filepath
        self.lineno = lineno
        self.log_path = log_path
        self.min_interval = min_interval
        LogFile.init_instance(log_path=self.log_path,
                              target_func=Function(name=self.func_name,
                                                   filepath=self.filepath,
                                                   lineno=self.lineno))

    def __call__(self, f):

        @wraps(f)
        def wrapper(*args, **kwargs):
            t1 = time.time() * 1000
            LogFile.get_instance().register()
            sys.settrace(trace_calls)
            result = f(*args, **kwargs)
            sys.settrace(None)
            t2 = time.time() * 1000
            if t2 - t1 >= self.min_interval:
                LogFile.get_instance().append(
                    f"{int(t2*1000)}  [PyProfiler] [{f.__name__}] totally {t2 - t1} ms coast\n"
                )
                LogFile.get_instance().commit()
            else:
                LogFile.get_instance().clean()
            return result

        return wrapper

    # def enable(self):
    #     """如果要分析项目中的所有函数，可以调用这个方法，启用全局性能分析。
    #     """
    #     sys.settrace(trace_calls)

    # def disable(self):
    #     """关闭全局性能分析
    #     """
    #     sys.settrace(None)