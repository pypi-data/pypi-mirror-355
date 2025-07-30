#!/usr/bin/python
# -*- coding: UTF-8 -*-

import types
import json
import time
import random
import traceback
from threading import RLock

from jxWebUI.ui_web.jxUtils import logger, checkAssert, Now, ValueType, base64_encode

'''
用来函数式定义web组件
'''
class WO_Func:
    pre_define_attrs = {}
    def __init__(self, type, name):
        self.type = type
        self.name = name
        self.attrs = {}

        self._current_attr = None

    def set_attr_value(self, value):
        ad = self.__class__.pre_define_attrs.get(self._current_attr)
        at = ad.get('type')
        if at == 'string' or at == 'datetime':
            self.attrs[self._current_attr] = f'"{str(value)}"'
        elif at == 'int':
            self.attrs[self._current_attr] = int(value)
        elif at == 'float':
            self.attrs[self._current_attr] = float(value)
        elif at == 'bool':
            if isinstance(value, bool):
                if value:
                    self.attrs[self._current_attr] = 'true'
                else:
                    self.attrs[self._current_attr] = 'false'
            else:
                self.attrs[self._current_attr] = str(value)
        elif at == 'json':
            self.attrs[self._current_attr] = json.dumps(value)
        else:
            raise Exception(f'不支持的类型：{at}')

    def __getattr__(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        ad = self.__class__.pre_define_attrs.get(name, None)
        checkAssert(ad is not None, f'未定义属性：{name}')
        self._current_attr = name
        return self.set_attr_value


class DataTable(WO_Func):
    pre_define_attrs = {}
    def __init__(self, name):
        super().__init__('dataTable', name)
        self.children_is_cs = True
        self.children_is_col = True

class Div(WO):
    def __init__(self, name, attrs):
        super().__init__('div', name, attrs)
        self.children_is_cs = True


class ShortCutTree:
    class Node:
        def __init__(self, ty, label, **attrs):
            self.type = ty
            self.text = label
            self.attrs = attrs
            self.nodes = {}

    def __init__(self):
        self.nodes = {}

    def toJson(self):
        rs = {}
        ra = []
        rs['out'] = ra
        wo = {}
        ra.append(wo)
        wo['woID'] = 'shortCutTree'
        wo['attr'] = 'treeData'
        ro = {}
        wo['data'] = ro
        nodes = []
        ro['nodes'] = nodes
        for f in self.nodes.values():
            fo = {}
            nodes.append(fo)
            fo['type'] = f.type
            fo['text'] = f.text
            ns = []
            fo['nodes'] = ns
            for n in f.nodes.values():
                no = {}
                ns.append(no)
                no['type'] = n.type
                no['text'] = n.text
                for k, v in n.attrs.items():
                    no[k] = v
        return rs

    def add_item(self, folder, label, **attrs):
        n = self.nodes.get(folder, None)
        if n is None:
            n = ShortCutTree.Node('folder', folder)
            self.nodes[folder] = n
        sn = ShortCutTree.Node('item', label, **attrs)
        n.nodes[label] = sn

    def add_folder(self, label):
        n = ShortCutTree.Node('folder',label)
        self.nodes[label] = n


