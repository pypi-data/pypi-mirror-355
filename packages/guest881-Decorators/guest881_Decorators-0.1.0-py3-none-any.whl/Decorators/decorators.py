# -*- coding: utf-8 -*-
"""
Created on 2025/6/15 18:05
@author: guest881
自用简易多功能装饰器模块
"""
from typing import Callable,Union
from functools import wraps
from time import sleep,perf_counter
from inspect import getsourcefile,getsourcelines
class Decorators:
    @staticmethod
    def repeat(num):
        """
        遇到异常会终止整个程序
        :param num:
        :return:
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                value=[func(*args,**kwargs) for _ in range(num)]
                return value
            return wrapper
        return decorator
    @staticmethod
    def cache(func:Callable):
        """
        斐波那契数列用嘎嘎爽
        无异常处理，遇到异常整个程序终止
        :param func:
        :return:
        """
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            key=str(args)+str(kwargs)
            if key not in cache:
               cache[key]=func(*args, **kwargs)
            return cache[key]
        return wrapper

    @staticmethod
    def retry(retries=1,delay=0):
        """
        静默处理异常
        requests请求嘎嘎好用
        :param retries:
        :param delay:
        :return:
        """
        def decorator(func:Callable):
            error_counts=0
            error_list=[]
            @wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal retries,error_counts
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_list.append(e)
                    if error_counts>0 and retries==0:
                        print(f"重试{error_counts}次，仍无法正常运行，请检查代码或环境问题，异常次数:{error_counts+1}，异常列表:\n{error_list}")
                        return
                    error_counts += 1
                    sleep(delay)
                    retries=retries-1
                    return wrapper(*args, **kwargs)
            return wrapper
        return decorator
    @staticmethod
    def get_time(func:Callable):
        """
        获取执行时长
        无异常处理
        可叠加装饰器使用
        :param func:
        :return:
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start=perf_counter()
            value=func(*args, **kwargs)
            end=perf_counter()
            print(f"执行总耗时{end-start:.5f}s")
            return value
        return wrapper
    @staticmethod
    def delay(sleep_time:Union[int,float]):
        """
        延时
        无异常处理
        :param sleep_time:
        :return:
        """
        def decorator(func:Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                sleep(sleep_time)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    @staticmethod
    def deprecated(message:str='',version:Union[int,float]=''):
        """
        弃用必备
        无异常处理
        :param message:
        :param version:
        :return:
        """
        def decorator(func:Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                file_path=getsourcefile(func)
                line_num=getsourcelines(func)
                print(
                    f"Deprecated warning:\n{file_path}:{line_num[1]}:{func.__name__} has been deprecated in {version} version \n{message}"
                )
                return func(*args, **kwargs)
            return wrapper
        return decorator