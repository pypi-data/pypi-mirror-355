# -*- coding: utf-8 -*-
"""
Created on 2025/6/15 18:05
@author: guest881
自用简易多功能装饰器模块
"""
from sys import stdout
from loguru import logger
from itertools import repeat
from typing import Callable,Union
from functools import wraps
from time import perf_counter,sleep
from datetime import datetime
import pickle
import os
import atexit


logger.remove()
logger.add(stdout,format="| <green>{time:%Y-%m-%d %H:%M:%S}</green> | <level>{level}</level> | <magenta>{message}</magenta>",colorize=True)
class Decorators:
    __cache={}
    file_path=None
    persist=False
    @staticmethod
    def get_original_function(func):
        """递归解包所有__wrapped__层，获取最原始的函数"""
        while hasattr(func, '__wrapped__'):
            func = func.__wrapped__
        return func
    @staticmethod
    def except_error(func:Callable):
        """
        懒得写try-except的时候，
        还想捕获异常继续执行程序，
        一个装饰器会美观很多
        :param func:
        :return:
        """
        @wraps(func)
        def wrapper(*args,**kwargs):
            try:
                return func(*args,**kwargs)
            except Exception as e:
                file_path = Decorators.get_original_function(func).__code__.co_filename
                line_num = Decorators.get_original_function(func).__code__.co_firstlineno
                logger.info(f'\n捕获位置:{file_path}:{line_num}'
                            f'\n捕获函数:{func.__name__}'
                            f'\n已捕获---->{e}')
        return wrapper
    @staticmethod
    def repeat(num:Union[int,float]):
        """
        遇到异常会终止整个程序
        :param num:
        :return:
        """
        num =num if isinstance(num, int) else int(num)
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):

                value=[func(*args,**kwargs) for _ in repeat(None,num)]
                return value
            return wrapper
        return decorator
    @staticmethod
    def cache(persist=False,file_path:str=None):
        """
        斐波那契数列用嘎嘎爽
        静默处理，遇到异常整个程序终止
        :param file_path:
        :param persist:
        :return:
        """

        Decorators.file_path=file_path

        def decorator(func:Callable):
            func_name = Decorators.get_original_function(func).__name__
            if persist:
                Decorators.persist=True
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            Decorators.__cache.update(pickle.load(f))
                            cache=Decorators.__cache.get(func_name)
                    else:
                        cache={}
                except Exception as e:
                    logger.error(e)
            else:
                cache= {}
            @wraps(func)
            def wrapper(*args, **kwargs):
                key=str(args)+str(kwargs)
                start=perf_counter()
                if key not in cache:
                    try:
                       cache[key]=func(*args, **kwargs)
                       Decorators.__cache.update({func_name: cache})
                    except Exception as e:
                        logger.error(f'\n{e} 请修正函数后再调用cache，否则可能会出现一些意想不到的问题')
                else:
                    end=perf_counter()
                    logger.info(f'命中缓存，执行时间{end-start}s')
                return Decorators.__cache[func_name][key]
            return wrapper
        return decorator
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
                    for _ in repeat(None,retries):
                        retries-=1
                        try:
                            sleep(delay)
                            return func(*args, **kwargs)
                        except Exception as e:
                            error_counts += 1
                            error_list.append(e)
                            requires=[error_counts>0,retries==0]
                            if all(requires):
                                logger.info(f"\n重试{error_counts}次，仍无法正常运行，请检查代码或环境问题，"
                                            f"\n异常次数:{error_counts+1}，"
                                            f"\n异常列表:"
                                            f"\n{error_list}")
                                return error_list
            return wrapper
        return decorator
    @staticmethod
    def get_time(exec_time=False):
        """
        获取执行时长
        无异常处理
        可叠加装饰器使用
        :param exec_time:
        :return:
        """
        def decorator(func:Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                file_path = Decorators.get_original_function(func).__code__.co_filename
                line_num = Decorators.get_original_function(func).__code__.co_firstlineno
                logger.info(f'\nStarted at {datetime.now():%H:%M:%S}')
                start=perf_counter()
                value=func(*args, **kwargs)
                end=perf_counter()
                logger.info(f'\nEnded at {datetime.now():%H:%M:%S}')
                if exec_time:
                    logger.info(f"\n抛出位置:{file_path}:{line_num}"
                            f"\n抛出函数:{func.__name__}"
                            f"\nmessage:执行总耗时{end-start}s")
                return value
            return wrapper
        return decorator
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
                file_path=Decorators.get_original_function(func).__code__.co_filename
                line_num=Decorators.get_original_function(func).__code__.co_firstlineno
                logger.warning(
                    f"\nDeprecated warning:"
                    f"\n抛出位置:{file_path}:{line_num}"
                    f"\n抛出函数:{func.__name__}"
                    f"\nmessage:{func.__name__} will be deprecated in {version} version {message}"
                )
                return func(*args, **kwargs)
            return wrapper
        return decorator
    @staticmethod
    def save_data():
        if Decorators.persist:
            if Decorators.file_path:
                with open(Decorators.file_path,'wb') as f:
                    pickle.dump(Decorators.__cache,f)
atexit.register(Decorators.save_data)