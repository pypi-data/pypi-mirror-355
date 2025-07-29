# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:07
@author: guest881
"""
from typing import Type
from .linkListStype import *
from .linkListsRegister import Register
class LinkListsManager:
    def __init__(self, node_type: Type[RegularListNode], link_name):
        self.link_name = link_name
        self.node_type:Type[RegularListNode]= node_type
        self.register = Register(link_name)

    def __call__(self, value=None):
        if value is None:
            raise ValueError('空实例不可调用方法')
        node = self.node_type(self.register, value)
        return node