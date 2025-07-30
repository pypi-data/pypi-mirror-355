# -*- coding: utf-8 -*-
"""
Created on 2025/6/15 19:42
@author: guest881
"""

from Decorators import *
@Decorators.get_time()
@Decorators.retry(3,0.5)
def fabonacci(n:int)->int:
    """生成斐波那契数列第N项"""
    if n<2:
        return n
    return fabonacci(n-1)+fabonacci(n-2)
fabonacci(1)
from requests import get
@Decorators.get_time(True)
@Decorators.cache(persist=True,file_path='cache.pkl')
def get_status(url):
    return get(url)
get_status("https://www.baidu.com")
print(get_status("https://www.baidu.com").url)