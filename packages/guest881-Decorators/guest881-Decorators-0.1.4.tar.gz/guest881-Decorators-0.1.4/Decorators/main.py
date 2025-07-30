# -*- coding: utf-8 -*-
"""
Created on 2025/6/15 19:42
@author: guest881
"""

from Decorators import *
@Decorators.except_error
@Decorators.cache
def fabonacci(n:int)->int:
    """生成斐波那契数列第N项"""
    if n<2:
        raise ValueError("Bob回家吧")
    return fabonacci(n-1)+fabonacci(n-2)
fabonacci(3)