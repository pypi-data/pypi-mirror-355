# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:05
@author: guest881
"""
class Register(list):
    storage = dict()
    def __init__(self, link_name: str) -> None:
        super().__init__()
        self.link_name = link_name
        if link_name in self.storage:
            raise KeyError('命名重复')
        self.storage.update({link_name: self})