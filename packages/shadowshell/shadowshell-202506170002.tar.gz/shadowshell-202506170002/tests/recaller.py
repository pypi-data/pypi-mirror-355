#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from base_test import BaseTest
from src.shadowshell.model.tree import Tree, TreeNode
from src.shadowshell.file import FileUtil
from src.shadowshell.monitor import function_monitor
from src.shadowshell.logging import LoggerFactory

class Recaller():

    __work_dir = "/Users/shadowwalker/shadowshellxyz/ai-cloudkeeper-assets/kb/globalic/0000@留存线索录房示例"

    def __init__(self):
        self.tree = Tree(self.__work_dir, "0000@留存线索录房示例")
        self.tree.build(self.tree.root, [(lambda node: self.__parse_out_code(node))])

    def __parse_out_code(self, node):
        if node is None or node.name is None or node.name.find("@") == -1:
            return None
        
        node.out_code = node.name.split("@")[0]

    @function_monitor("Recaller")
    def recall(self, code):
        node = self.tree.find_by_out_code(code)
        if node is None or node.leaf == True or node.children is None:
            return None
        
        examples = ""
        for child in node.children:
            if child.leaf == False:
                file_name = ("%s/%s" % (child.code, "业主意图示例.md"))
                part_examples = FileUtil.get_all(file_name);
                examples = f'{examples}\n场景编码:{child.out_code}\n{part_examples}\n'
            
        return examples
        

        #  List<TreeNode> grandNodes = child.getGrandNodes();
        #     String fileName = Optional.ofNullable(grandNodes).orElse(new ArrayList<>(0)).stream().map(TreeNode::getName)
        #             .collect(Collectors.joining("/"));
        #     LoggerUtil.info(logger, "fileName -> {0}", fileName);
        #     fileName = MessageFormat.format("{0}/kb/globalic/{1}/{2}", WORK_DIR, fileName, "业主意图示例.md");

        #     LoggerUtil.info(logger, "fileName -> {0}", fileName);

        #     String content = FileUtil.getContent(fileName, "\n");
        #     String childIntentCode = child.getName().split("@")[0];
        #     return MessageFormat.format("\n意图编码[{0}]\n意图名称[{1}]\n{2}", childIntentCode, child.getName(), content);


logger = LoggerFactory.get_logger()
Recaller().recall("10")


