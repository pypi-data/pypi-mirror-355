#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这是一个简单的setup.py文件，用于兼容传统安装方式。
实际配置在pyproject.toml中定义。
"""

import os
import setuptools
from setuptools import find_packages


# 递归查找所有非Python文件作为数据文件
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            if not filename.endswith('.py') and not filename.endswith('.pyc'):
                rel_path = os.path.join(path, filename)
                rel_dir = os.path.relpath(os.path.dirname(rel_path), 'minimax_qa_mcp')
                if not rel_dir.startswith('.') and not rel_dir.startswith('__'):
                    paths.append(os.path.join(rel_dir, os.path.basename(rel_path)))
    return paths


if __name__ == "__main__":
    # 自动发现所有包
    packages = find_packages(include=['minimax_qa_mcp', 'minimax_qa_mcp.*'])
    
    # 查找所有配置文件和其他资源
    package_data = {
        'minimax_qa_mcp': package_files('minimax_qa_mcp')
    }
    
    # 设置
    setuptools.setup(
        packages=packages,
        package_data=package_data,
        include_package_data=True,
    ) 