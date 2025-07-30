# -*- coding: utf-8 -*-
"""
Created on 2025/6/15 19:42
@author: guest881
"""

from Decorators import *
from time import sleep
@Decorators.get_time
@Decorators.retry(3,1)
@Decorators.deprecated()
def test_main():
    # value='123'
    return '123'

test_main()