# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:03
@author: guest881
"""
class LinkListsBase:
    def __init__(self, register,value) -> None:
        self.register=register
        self.value = value
        self.next = ...
        register.append(self)