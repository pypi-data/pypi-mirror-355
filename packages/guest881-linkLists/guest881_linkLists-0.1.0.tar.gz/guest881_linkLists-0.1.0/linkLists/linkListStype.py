# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:04
@author: guest881
"""
from typing import Self
from .linkListsRegister import Register
from .linkListsBase import LinkListsBase
class RegularListNode(LinkListsBase):
    last = ...
    def __init__(self, register: Register, value) -> None:
        super().__init__(register, value)
        if self.length >= 2:
            RegularListNode.last = register[-1]
            previous = register[-2]
            previous.next = self.last
    def add_node(self, value) -> Self:
        if self.next is not ...:
            raise ValueError("操作将覆盖链表")
        self.next = RegularListNode(self.register, value)
        return self.next

    def cut_node(self) -> Self:
        index = self.register.index(self)
        del self.register[index:]
        return self

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

    def insert_node(self, other: Self, index: int) -> Self:

        if self.register == other.register:
            last = self.variable_node(index + 1)
            previous = self.variable_node(index - 1)
            self.register.insert(index, other)
            previous.next = other
            other.next = last
            return self
        else:
            raise KeyError('register不匹配')
    @property
    def map_link(self):
        map_list = []
        if self.register:
            tmp = self.register[0]
        else:
            return
        count = 0
        length = self.length
        while tmp is not ... and count <= length:
            map_list.append(str(tmp.value))
            tmp = tmp.next
            count += 1
        return '->'.join(map_list)
class CircularListNode(RegularListNode):
    def __init__(self, register, value) -> None:
        super().__init__(register, value)
        if self.length >= 2:
            CircularListNode.last = self.register[-1]
            CircularListNode.last.next = self.register[0]

    def insert_node(self, other: Self, index: int) -> Self:
        if self.register==other.register:
            self.register.pop()
            self.register[-1].next=self.register[0]
            self.register.insert(index, other)
            previous = self.variable_node(index - 1)
            previous.next = other
            if index >=self.length - 1:
                other.next = self.register[0]
                return self
            last = self.variable_node(index + 1)
            other.next = last
            return self
        else:
            raise KeyError('register不匹配')

    def add_node(self, value) -> Self:
        self.next = CircularListNode(self.register, value)
        return self.next

    def cut_node(self) -> Self:
        index = self.register.index(self)
        previous = self.register[index - 1]
        previous.next = self.register[0]
        del self.register[index:]
        return self