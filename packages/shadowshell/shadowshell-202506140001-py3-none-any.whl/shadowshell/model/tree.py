#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: shadowshell
"""

"""
多树节点
"""

from collections import deque
import os

class TreeNode2():

    def __init__(self):
        pass

class TreeNode():

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.parent = None
        self.type = None
        self.out_code = None
        self.full_name = None
        self.leaf = False
        self.content  = None
        pass

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

class Tree():

    def __init__(self, code, name):
        self.root = TreeNode(code, name)
        pass

    def build(self, parent_node):
        children = self.list_children(parent_node.code)
        if children is None:
            parent_node.leaf = True
            return
        for child in children:
            parent_node.add_child(child)
            self.build(child)
        pass

    def list_children(self, parent_code):
        children = []
        for item in os.listdir(parent_code):
            child = TreeNode(os.path.join(parent_code, item), item)
            children.append(child)
        pass

    def bfs_traverse(self, root, funcs):
        if root is None:
            return
        
        queue = deque()
        queue.append(root)

        while queue:
            node = queue.popleft()
            if funcs is not None:
                for func in funcs:
                    func(node)
            queue.extend(node.children)
        pass

    def get_root(self):
        return self.root

