# -*- coding: utf-8 -*-
"""
Created on 2025/6/15 19:42
@author: guest881
"""

from Decorators import *
@Decorators.retry(3,0.5)
def fabonacci(n:int)->int:
    """生成斐波那契数列第N项"""
    if n<2:
        raise n
    return fabonacci(n-1)+fabonacci(n-2)
fabonacci(1)