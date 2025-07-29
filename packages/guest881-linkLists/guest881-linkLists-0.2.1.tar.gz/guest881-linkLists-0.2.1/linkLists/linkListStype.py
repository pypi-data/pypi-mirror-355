# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:04
@author: guest881
"""
from typing import Self,Union
from .linkListsRegister import Register
from .linkListsBase import LinkListsBase

class RegularListNode(LinkListsBase):
    """
    用于实现最基本的链表节点的父类
    self.add_node(self,value)->Self在当前节点后追加一个节点并返回追加的节点
    self.cut_node(self) -> None从当前节点开始截断链表，包含自身
    self.previous_node(self) -> Self返回上一个节点
    self.first_node(self) -> Self返回首节点
    self.last_node(self) -> Self返回最后一个节点
    self.variable_node(self, index: int) -> Self返回指定索引的节点
    self返回self.value
    self.length返回链表长度
    self.index返回实例所在索引
    self.map_link返回链表结构
    self.insert_node(self, value:Union[str,list,dict,set,tuple,float,int], index: int) -> Self指定位置插入节点，不允许传入节点类实例
    用法见main文件。
    操作流程：
    先实例化一个链表对象LinkManager，传入节点类型类，传入链表名
    接着调用LinkManager的实例创建链表节点
    示例代码：
    from linkLists import *
    # 初始化循环链表
    circular_link1 = LinkListsManager(CircularListNode, 'circular_link1')
    cnode1 = circular_link1('Hello')
    for i in range(5):
        cnode1 = cnode1.add_node(i)
    print(cnode1.map_link)#  Hello->0->1->2->3->4->Hello
    """
    def __init__(self, register: Register, value,skip_optional=False) -> None:
        super().__init__(register, value)

        self.wait_node = None
        self.map_list = None
        if not skip_optional:
            self.register.append(self)
        if self.length >= 2:
            self.last = register[-1]
            self.previous = register[-2]
            self.previous.next = self.last
    def add_node(self, value) -> Self:
        if self.next is not ...:
            raise ValueError("操作将覆盖链表")
        self.next = RegularListNode(self.register, value)
        return self.next

    def cut_node(self) -> None:
        index = self.register.index(self)
        del self.register[index:]
        return

    def previous_node(self) -> Self:
        index = self.register.index(self)
        return self.register[index - 1]

    def first_node(self) -> Self:
        return self.register[0]

    def last_node(self) -> Self:
        return self.register[-1]

    def variable_node(self, index: int) -> Self:
        return self.register[index]

    @property
    def length(self) -> int:
        return len(self.register)

    @property
    def index(self) -> int:
        return self.register.index(self)

    def insert_node(self, value:Union[str,list,dict,set,tuple,float,int], index: int) -> Self:
        if isinstance(value, RegularListNode):
            raise ValueError("禁止传入节点实例对象")
        self.wait_node=RegularListNode(self.register,value, True)
        return self.edge_process(index)
    def edge_process(self,index)->Self:
        if self.length == 0:
            self.register.append(self.wait_node)
            return self.wait_node
        if self.length==1 and index<=self.length:
            raise IndexError("操作将覆盖节点，如果想删除，请用cut_node")
        self.register.insert(index, self.wait_node)
        #处理末尾插入
        if index>=self.length-1:
            self.register[self.length-2].next = self.wait_node
            self.wait_node.next = ...
            return self

        if index==-1:
            self.last.next = ...
            self.wait_node.next = self.register[-1]
            self.register[index-1].next = self.wait_node
        # 处理中间插入
        if 1 <= index < self.length-1 or -1 > index > -(self.length - 1):
            self.wait_node.next = self.register[index + 1]
            self.register[index-1].next = self.wait_node
            return self
        #处理开头插入
        else:
            self.wait_node.next = self.register[index + 1]
            return self

    @property
    def map_link(self):
        self.map_list = []
        if self.register:
            tmp = self.register[0]
        else:
            return
        count = 0
        length = self.length
        while tmp is not ... and count <= length:
            self.map_list.append(str(tmp.value))
            tmp = tmp.next
            count += 1
        return '->'.join(self.map_list)
    def __repr__(self):
        return f'value:{self.value}'
    __str__ = __repr__
class CircularListNode(RegularListNode):
    """
    尾节点的next指针指向首节点，具体方法属性见RegularListNode
    """
    def __init__(self, register, value,skip_optional=False) -> None:
        super().__init__(register, value,skip_optional)
        if self.length >= 2:
            self.last = self.register[-1]
            self.last.next = self.register[0]

    def insert_node(self, value:Union[str,list,dict,set,tuple,float,int], index: int) -> Self:
        if isinstance(value, RegularListNode):
            raise ValueError("禁止传入节点实例对象")
        self.wait_node = CircularListNode(self.register, value, True)
        if self.length == 1 and index <= self.length:
            raise IndexError("操作将覆盖节点，甚至越界，如果想删除，请用cut_node")
        if self.length == 0:
            self.register.append(self.wait_node)
            return self.wait_node
        self.register.insert(index, self.wait_node)
        # 处理末尾插入
        if index >= self.length - 1 :
            self.register[self.length - 2].next = self.wait_node
            self.wait_node.next = self.register[0]
            return self
        if index==-1:
            self.register[self.length-3].next = self.register[self.length-2]
            self.register[self.length-2].next = self.register[self.length-1]
            return self
        # 处理中间插入
        if 1 <= index < self.length - 1 or -1 > index > -(self.length - 1):
            self.wait_node.next = self.register[index + 1]
            self.register[index - 1].next = self.wait_node
            return self
        # 处理开头插入
        else:
            self.wait_node.next = self.register[1]
            self.last = self.register[-1]
            self.last.next = self.register[0]
            return self
    def add_node(self, value) -> Self:
        self.next = CircularListNode(self.register, value)
        self.next.next = self.register[0]
        return self.next

    def cut_node(self) -> Union[Self,None]:
        index = self.register.index(self)
        previous = self.register[index - 1]
        previous.next = self.register[0]
        del self.register[index:]
        return
    def __repr__(self):
        return f'value:{self.value}'

    __str__ = __repr__
class UniqueListNode(RegularListNode):
    """
    去重链表，尾节点指向...，具体方法属性见RegularListNode
    """
    value_check=set()
    def __init__(self, register, value) -> None:
        super().__init__(register, value,skip_optional=True)
        if not value in UniqueListNode.value_check:
            UniqueListNode.value_check.add(value)
            register.append(self)
        else:
            return
    def add_node(self, value) -> Self:
        self.next = UniqueListNode(self.register, value)
        return self.next
    def insert_node(self, value:Union[str,list,dict,set,tuple,float,int], index: int) -> Self:
        if isinstance(value, RegularListNode):
            raise ValueError("禁止传入节点实例对象")
        if value in UniqueListNode.value_check:
            return self
        self.wait_node = UniqueListNode(self.register, value)
        return self.edge_process(index)
    def __repr__(self):
        return f'value:{self.value}'
    __str__ = __repr__
