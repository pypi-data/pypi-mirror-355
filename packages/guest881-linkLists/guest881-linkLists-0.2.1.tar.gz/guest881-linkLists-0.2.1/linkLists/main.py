# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:22
@author: guest881
"""

from linkLists import *

# 初始化循环链表
circular_link1 = LinkListsManager(CircularListNode, 'circular_link1')
cnode1 = circular_link1('Hello')
for i in range(5):
    cnode1 = cnode1.add_node(i)
print(RegularListNode.__doc__)