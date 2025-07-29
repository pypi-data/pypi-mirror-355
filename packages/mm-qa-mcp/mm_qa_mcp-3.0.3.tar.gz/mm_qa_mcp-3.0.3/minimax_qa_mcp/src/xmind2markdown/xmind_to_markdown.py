#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
XMind思维导图转换为Markdown文件工具
增强版 - 支持更多XMind元素、批量处理和进度显示
保留原始XMind文件，可选择创建备份
"""

import os
import sys
import json
import zipfile
import shutil
import tempfile
import glob
import argparse
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree import ElementTree as ET
import base64


class XMindToMarkdown:
    def __init__(self, xmind_file, indent_style="  ", image_dir=None, backup_original=False):
        """初始化转换器

        Args:
            xmind_file (file): XMind文件
            indent_style (str, optional): Markdown列表缩进样式. 默认为两个空格.
            image_dir (str, optional): 图片保存目录. 如果不指定，则使用Markdown文件相同目录下的images文件夹.
            backup_original (bool, optional): 是否创建原始文件的备份. 默认为False.
        """
        self.xmind_file = xmind_file
        self.temp_dir = tempfile.mkdtemp()
        self.content_json = None
        self.content_xml = None
        self.markdown_content = []
        self.indent_style = indent_style
        self.image_dict = {}  # 存储图片信息 {image_id: image_path}
        self.topic_images = {}  # 存储主题与图片的关联 {topic_id: [image_paths]}
        self.notes_dict = {}  # 存储备注信息
        self.link_dict = {}   # 存储链接信息
        self.backup_original = backup_original
        self.backup_file = None  # 备份文件路径
        
        # 设置图片目录
        if image_dir:
            self.image_dir = image_dir
        else:
            md_dir = os.path.dirname(os.path.abspath(
                os.path.splitext(self.xmind_file)[0] + '.md'
            ))
            self.image_dir = os.path.join(md_dir, 'images')
        
        # 确保图片目录存在
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        # 如果需要，创建原始文件的备份
        if self.backup_original:
            self._backup_original_file()
        
    @staticmethod
    def from_file_object(file_obj, output, indent_style="  ", image_dir=None, backup_original=False):
        """从文件对象创建XMindToMarkdown实例并进行转换
        
        Args:
            file_obj: 输入的文件对象，支持多种类型:
                - 类文件对象(有read方法)
                - 包含content字段的字典
                - 字节内容(bytes)
                - 文件路径字符串(str)
            output (str): 输出的Markdown文件名称（必传参数）
            indent_style (str, optional): Markdown列表缩进样式，默认为两个空格
            image_dir (str, optional): 图片保存目录，如不指定则使用Markdown文件相同目录下的images文件夹
            backup_original (bool, optional): 是否创建原始文件的备份，默认为False
            
        Returns:
            dict: 包含生成的Markdown文件路径、内容和图片信息
        """
        try:
            # 创建临时文件保存上传的文件内容
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.xmind")
            
            # 保存文件内容到临时文件
            with open(temp_file_path, 'wb') as temp_file:
                # 根据file_obj对象的类型进行不同处理
                if hasattr(file_obj, 'read'):
                    # 如果是类文件对象，直接读取内容
                    temp_file.write(file_obj.read())
                elif isinstance(file_obj, dict) and 'content' in file_obj:
                    # 如果是包含内容的字典
                    temp_file.write(file_obj['content'])
                elif isinstance(file_obj, bytes):
                    # 如果是字节内容
                    temp_file.write(file_obj)
                elif isinstance(file_obj, str):
                    # 如果是文件路径字符串
                    if os.path.exists(file_obj):
                        with open(file_obj, 'rb') as src_file:
                            temp_file.write(src_file.read())
                    else:
                        return {"error": f"文件 '{file_obj}' 不存在"}
                else:
                    return {"error": "不支持的文件类型"}
            
            # 执行转换
            converter = XMindToMarkdown(
                temp_file_path,
                indent_style=indent_style,
                image_dir=image_dir,
                backup_original=backup_original
            )
            
            # 获取转换后的Markdown内容，但不保存到文件
            markdown_content = converter.convert()
            
            # 收集图片内容
            image_contents = {}
            # 遍历所有提取出的图片
            for image_id, image_path in converter.image_dict.items():
                if os.path.exists(image_path):
                    # 读取图片文件内容
                    with open(image_path, 'rb') as img_file:
                        # 使用相对路径作为键
                        rel_path = converter._get_relative_image_path(image_path)
                        # 将图片内容编码为base64字符串
                        image_contents[rel_path] = base64.b64encode(img_file.read()).decode('utf-8')
            
            # 清理临时文件
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            return {
                "markdown_file_path": output,
                "markdown_content": markdown_content,
                "image_file_path": converter.image_dir,
                "image_content": image_contents
            }
        except Exception as e:
            return {"error": f"转换失败: {str(e)}"}
        
    def _backup_original_file(self):
        """创建原始XMind文件的备份"""
        base_name = os.path.basename(self.xmind_file)
        backup_dir = os.path.join(os.path.dirname(self.xmind_file), 'xmind_backups')
        
        # 确保备份目录存在
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # 创建带有时间戳的备份文件名
        file_name, file_ext = os.path.splitext(base_name)
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        backup_name = f"{file_name}_{timestamp}{file_ext}"
        self.backup_file = os.path.join(backup_dir, backup_name)
        
        # 复制文件
        shutil.copy2(self.xmind_file, self.backup_file)
    
    def __del__(self):
        """清理临时文件夹"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def extract_xmind(self):
        """解压XMind文件到临时目录"""
        try:
            with zipfile.ZipFile(self.xmind_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # XMind Zen (新版XMind)使用content.json
            content_json_path = os.path.join(self.temp_dir, 'content.json')
            
            # XMind 8 (旧版XMind)使用content.xml
            content_xml_path = os.path.join(self.temp_dir, 'content.xml')
            
            if os.path.exists(content_json_path):
                # 处理XMind Zen格式
                with open(content_json_path, 'r', encoding='utf-8') as f:
                    self.content_json = json.load(f)
                return 'json'
            elif os.path.exists(content_xml_path):
                # 处理XMind 8格式
                self.content_xml = content_xml_path
                return 'xml'
            else:
                raise Exception("无法识别的XMind文件格式")
        except zipfile.BadZipFile:
            raise Exception(f"文件 '{self.xmind_file}' 不是有效的XMind文件")
        except Exception as e:
            raise Exception(f"解压XMind文件失败: {str(e)}")
    
    def extract_resources(self):
        """提取XMind文件中的资源（如图片）"""
        resources_dir = os.path.join(self.temp_dir, 'resources')
        attachments_dir = os.path.join(self.temp_dir, 'attachments')
        
        # 处理resources目录下的图片
        if os.path.exists(resources_dir):
            for root, _, files in os.walk(resources_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp')):
                        # 获取图片ID（文件名）
                        image_id = file
                        src_path = os.path.join(root, file)
                        # 创建目标路径
                        unique_name = f"{str(uuid.uuid4())[:8]}_{file}"
                        dest_path = os.path.join(self.image_dir, unique_name)
                        # 复制文件
                        shutil.copy2(src_path, dest_path)
                        # 存储映射
                        self.image_dict[image_id] = dest_path
        
        # 处理attachments目录下的图片
        if os.path.exists(attachments_dir):
            for root, _, files in os.walk(attachments_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp')):
                        # 获取图片ID（文件名）
                        image_id = file
                        src_path = os.path.join(root, file)
                        # 创建目标路径
                        unique_name = f"{str(uuid.uuid4())[:8]}_{file}"
                        dest_path = os.path.join(self.image_dir, unique_name)
                        # 复制文件
                        shutil.copy2(src_path, dest_path)
                        # 存储映射
                        self.image_dict[image_id] = dest_path
    
    def parse_json_content(self):
        """解析XMind Zen格式的content.json文件"""
        if not self.content_json:
            return
        
        # 尝试提取备注、链接和图片信息
        self._extract_notes_json()
        self._extract_images_json()
        
        # 处理所有画布
        for sheet_index, sheet in enumerate(self.content_json):
            # 添加画布标题
            sheet_title = sheet.get('title', f'画布 {sheet_index + 1}')
            self.markdown_content.append(f"# {sheet_title}\n")
            
            # 处理根主题（attached类型的主题）
            root_topic = sheet.get('rootTopic', {})
            if root_topic:
                self._parse_topic_json(root_topic, 0)
                
                # 处理同一画布内的其他主题（detached类型的主题）
                detached_topics = []
                
                # 检查是否有独立主题
                if 'children' in root_topic and 'detached' in root_topic['children']:
                    detached_topics = root_topic['children']['detached']
                
                # 如果找到了独立主题
                if detached_topics:
                    self.markdown_content.append("\n## 其他主题\n")
                    for topic in detached_topics:
                        topic_title = topic.get('title', '未命名主题')
                        self.markdown_content.append(f"\n### {topic_title}\n")
                        self._parse_topic_json(topic, 0)
            
            # 如果不是最后一个画布，添加分隔符
            if sheet_index < len(self.content_json) - 1:
                self.markdown_content.append("\n---\n")
    
    def _extract_notes_json(self):
        """从JSON中提取备注信息"""
        for sheet in self.content_json:
            self._extract_notes_from_topic_json(sheet.get('rootTopic', {}))
    
    def _extract_images_json(self):
        """从JSON中提取图片信息"""
        for sheet in self.content_json:
            self._extract_images_from_topic_json(sheet.get('rootTopic', {}))
    
    def _extract_images_from_topic_json(self, topic):
        """递归从主题中提取图片信息
        
        Args:
            topic (dict): 主题对象
        """
        if not topic:
            return
        
        # 提取主题ID
        topic_id = topic.get('id', '')
        
        # 检查是否有图片
        if 'image' in topic:
            image_data = topic['image']
            # 检查是否有src属性（指向图片路径）
            if 'src' in image_data:
                image_src = image_data['src']
                # 提取图片ID
                image_id = os.path.basename(image_src)
                
                # 关联主题与图片
                if topic_id not in self.topic_images:
                    self.topic_images[topic_id] = []
                self.topic_images[topic_id].append(image_id)
        
        # 处理子主题
        children = topic.get('children', {})
        if 'attached' in children and isinstance(children['attached'], list):
            for child in children['attached']:
                self._extract_images_from_topic_json(child)
    
    def _extract_notes_from_topic_json(self, topic):
        """递归从主题中提取备注信息
        
        Args:
            topic (dict): 主题对象
        """
        if not topic:
            return
        
        # 提取主题ID
        topic_id = topic.get('id', '')
        
        # 提取备注
        notes = topic.get('notes', {})
        if notes and 'plain' in notes and notes['plain'].get('content', ''):
            self.notes_dict[topic_id] = notes['plain']['content']
        
        # 提取超链接
        href = topic.get('href', '')
        if href:
            self.link_dict[topic_id] = href
        
        # 处理子主题
        children = topic.get('children', {})
        if 'attached' in children and isinstance(children['attached'], list):
            for child in children['attached']:
                self._extract_notes_from_topic_json(child)
    
    def _get_relative_image_path(self, image_path):
        """获取图片相对于Markdown文件的相对路径
        
        Args:
            image_path (str): 图片的绝对路径
            
        Returns:
            str: 图片的相对路径
        """
        md_dir = os.path.dirname(os.path.abspath(
            os.path.splitext(self.xmind_file)[0] + '.md'
        ))
        return os.path.relpath(image_path, md_dir)
    
    def _parse_topic_json(self, topic, level):
        """递归解析主题及其子主题，转换为Markdown格式
        
        Args:
            topic (dict): 主题对象
            level (int): 当前层级深度
        """
        if not topic:
            return
        
        # 获取主题ID和标题
        topic_id = topic.get('id', '')
        title = topic.get('title', '')
        
        # 处理主题中的换行，将换行转换为Markdown兼容的格式
        # 在Markdown中，需要使用两个空格加换行或空行来表示换行
        title = title.replace('\r\n', '\n')  # 统一换行符
        title_lines = title.split('\n')
        
        # 检查是否是纯列表格式（每行都以"-"开头）
        is_list_format = all(line.strip().startswith('-') for line in title_lines if line.strip())
        
        # 获取第一行内容
        formatted_title = title_lines[0] if title_lines else ""
        
        # 如果是列表格式，移除第一行的"-"前缀
        if is_list_format and formatted_title.strip().startswith('-'):
            formatted_title = formatted_title.strip()[1:].strip()
        
        # 处理优先级标记
        priority_prefix = ""
        if 'markers' in topic and isinstance(topic['markers'], list):
            for marker in topic['markers']:
                marker_id = marker.get('markerId', '')
                # 优先级映射 - 从XMind标记ID转为Markdown格式
                if marker_id == 'priority-1':
                    priority_prefix = "[!(p1)] "
                elif marker_id == 'priority-2':
                    priority_prefix = "[!(p2)] "
                elif marker_id == 'priority-3':
                    priority_prefix = "[!(p3)] "
        
        # 添加到Markdown内容中 - 第一行
        indent = self.indent_style * level
        md_line = f"{indent}- {priority_prefix}{formatted_title}"
        
        # 添加链接
        if topic_id in self.link_dict:
            link = self.link_dict[topic_id]
            md_line += f" [{link}]({link})"
        
        self.markdown_content.append(md_line)
        
        # 处理剩余的行（如果有多行）
        if len(title_lines) > 1:
            additional_indent = self.indent_style * (level + 1)
            for additional_line in title_lines[1:]:
                if not additional_line.strip():  # 跳过空行
                    continue
                    
                # 处理带有"-"前缀的行
                line_content = additional_line.strip()
                if is_list_format and line_content.startswith('-'):
                    # 保持列表格式，但增加缩进级别
                    line_content = line_content[1:].strip()  # 移除"-"符号
                    self.markdown_content.append(f"{additional_indent}- {line_content}")
                else:
                    # 普通文本行
                    self.markdown_content.append(f"{additional_indent}{line_content}")
        
        # 添加图片
        if topic_id in self.topic_images:
            for image_id in self.topic_images[topic_id]:
                if image_id in self.image_dict:
                    image_path = self.image_dict[image_id]
                    rel_path = self._get_relative_image_path(image_path)
                    img_indent = self.indent_style * (level + 1)
                    self.markdown_content.append(f"{img_indent}![{os.path.basename(image_path)}]({rel_path})")
        
        # 添加备注
        if topic_id in self.notes_dict:
            note_content = self.notes_dict[topic_id]
            note_lines = note_content.split('\n')
            note_indent = self.indent_style * (level + 1)
            
            # 添加备注块
            self.markdown_content.append(f"{note_indent}- 备注:")
            for note_line in note_lines:
                self.markdown_content.append(f"{note_indent}  {note_line}")
        
        # 处理子主题
        children = topic.get('children', {})
        if 'attached' in children and isinstance(children['attached'], list):
            for child in children['attached']:
                self._parse_topic_json(child, level + 1)
    
    def parse_xml_content(self):
        """解析XMind 8格式的content.xml文件"""
        try:
            tree = ET.parse(self.content_xml)
            root = tree.getroot()
            
            # 查找所有sheet元素
            ns = {'xmind': 'urn:xmind:xmap:xmlns:content:2.0'}
            sheets = root.findall('.//xmind:sheet', ns)
            
            for sheet_index, sheet in enumerate(sheets):
                # 添加画布标题
                title_elem = sheet.find('./xmind:title', ns)
                sheet_title = title_elem.text if title_elem is not None and title_elem.text else f'画布 {sheet_index + 1}'
                self.markdown_content.append(f"# {sheet_title}\n")
                
                # 找到所有普通主题（attached类型）
                main_topic = sheet.find('./xmind:topic', ns)
                if main_topic is not None:
                    self._parse_topic_xml(main_topic, 0, ns)
                
                # 查找并处理detached类型的主题（独立主题，如"组图生成"）
                detached_topics = sheet.findall('.//xmind:topics[@type="detached"]/xmind:topic', ns)
                
                # 如果找到了独立主题
                if detached_topics:
                    self.markdown_content.append("\n## 其他主题\n")
                    for topic in detached_topics:
                        title_elem = topic.find('./xmind:title', ns)
                        topic_title = title_elem.text if title_elem is not None and title_elem.text else "未命名主题"
                        self.markdown_content.append(f"\n### {topic_title}\n")
                        self._parse_topic_xml(topic, 0, ns)
                
                # 如果不是最后一个画布，添加分隔符
                if sheet_index < len(sheets) - 1:
                    self.markdown_content.append("\n---\n")
        except Exception as e:
            raise Exception(f"解析XML内容失败: {str(e)}")
    
    def _parse_topic_xml(self, topic, level, ns):
        """递归解析XML主题及其子主题
        
        Args:
            topic (Element): XML主题元素
            level (int): 当前层级深度
            ns (dict): 命名空间
        """
        title_elem = topic.find('./xmind:title', ns)
        if title_elem is not None and title_elem.text:
            # 获取主题标题
            title = title_elem.text
            
            # 处理主题中的换行，将换行转换为Markdown兼容的格式
            title = title.replace('\r\n', '\n')  # 统一换行符
            title_lines = title.split('\n')
            
            # 检查是否是纯列表格式（每行都以"-"开头）
            is_list_format = all(line.strip().startswith('-') for line in title_lines if line.strip())
            
            # 获取第一行内容
            formatted_title = title_lines[0] if title_lines else ""
            
            # 如果是列表格式，移除第一行的"-"前缀
            if is_list_format and formatted_title.strip().startswith('-'):
                formatted_title = formatted_title.strip()[1:].strip()
            
            # 处理优先级标记
            priority_prefix = ""
            marker_refs = topic.findall('./xmind:marker-refs/xmind:marker-ref', ns)
            for marker_ref in marker_refs:
                if 'marker-id' in marker_ref.attrib:
                    marker_id = marker_ref.attrib['marker-id']
                    # XMind 8中优先级标记的ID
                    if marker_id == 'priority-1':
                        priority_prefix = "[!(p1)] "
                    elif marker_id == 'priority-2':
                        priority_prefix = "[!(p2)] "
                    elif marker_id == 'priority-3':
                        priority_prefix = "[!(p3)] "
            
            # 添加到Markdown内容中 - 第一行
            indent = self.indent_style * level
            md_line = f"{indent}- {priority_prefix}{formatted_title}"
            
            # 检查是否有链接
            link = None
            hyperlink = topic.find('./xmind:hyperlink', ns)
            if hyperlink is not None and 'href' in hyperlink.attrib:
                link = hyperlink.attrib['href']
                md_line += f" [{link}]({link})"
            
            self.markdown_content.append(md_line)
            
            # 处理剩余的行（如果有多行）
            if len(title_lines) > 1:
                additional_indent = self.indent_style * (level + 1)
                for additional_line in title_lines[1:]:
                    if not additional_line.strip():  # 跳过空行
                        continue
                        
                    # 处理带有"-"前缀的行
                    line_content = additional_line.strip()
                    if is_list_format and line_content.startswith('-'):
                        # 保持列表格式，但增加缩进级别
                        line_content = line_content[1:].strip()  # 移除"-"符号
                        self.markdown_content.append(f"{additional_indent}- {line_content}")
                    else:
                        # 普通文本行
                        self.markdown_content.append(f"{additional_indent}{line_content}")
            
            # 检查是否有图片
            image = topic.find('.//xmind:image', ns)
            if image is not None and 'src' in image.attrib:
                image_src = image.attrib['src']
                image_id = os.path.basename(image_src)
                
                if image_id in self.image_dict:
                    image_path = self.image_dict[image_id]
                    rel_path = self._get_relative_image_path(image_path)
                    img_indent = self.indent_style * (level + 1)
                    self.markdown_content.append(f"{img_indent}![{os.path.basename(image_path)}]({rel_path})")
            
            # 检查是否有备注
            notes = topic.find('./xmind:notes', ns)
            if notes is not None:
                plain = notes.find('.//xmind:plain', ns)
                if plain is not None and plain.text:
                    note_content = plain.text
                    note_lines = note_content.split('\n')
                    note_indent = self.indent_style * (level + 1)
                    
                    # 添加备注块
                    self.markdown_content.append(f"{note_indent}- 备注:")
                    for note_line in note_lines:
                        self.markdown_content.append(f"{note_indent}  {note_line}")
            
            # 处理子主题
            children = topic.find('./xmind:children/xmind:topics[@type="attached"]', ns)
            if children is not None:
                for child_topic in children.findall('./xmind:topic', ns):
                    self._parse_topic_xml(child_topic, level + 1, ns)
    
    def convert(self):
        """执行转换过程"""
        try:
            # 提取XMind文件
            format_type = self.extract_xmind()
            
            # 提取资源
            self.extract_resources()
            
            # 解析内容
            if format_type == 'json':
                self.parse_json_content()
            elif format_type == 'xml':
                self.parse_xml_content()
            
            # 在Markdown文档开头添加原始文件信息
            source_info = [
                "<!-- ",
                f"转换自: {os.path.basename(self.xmind_file)}",
                f"转换时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
                "原始XMind文件已保留",
                " -->",
                ""
            ]
            
            # 将原始文件信息插入到Markdown内容的开头
            self.markdown_content = source_info + self.markdown_content
            
            # 返回Markdown内容
            return '\n'.join(self.markdown_content)
            
        except Exception as e:
            raise Exception(f"转换失败: {str(e)}")
    
    def save_markdown(self, output_file=None):
        """保存Markdown内容到文件
        
        Args:
            output_file (str, optional): 输出文件路径。如果未提供，将使用XMind文件名替换扩展名。
        
        Returns:
            str: 输出文件路径
        """
        if not output_file:
            base_name = os.path.splitext(self.xmind_file)[0]
            output_file = f"{base_name}.md"
        
        try:
            markdown_content = self.convert()
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            return output_file, markdown_content
        except Exception as e:
            raise Exception(f"保存Markdown文件失败: {str(e)}")


def is_valid_xmind_file(file_path):
    """验证文件是否为有效的XMind格式"""
    try:
        # 检查文件是否存在且可读
        if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
            return False
            
        # 检查文件大小
        if os.path.getsize(file_path) < 100:
            return False
        
        # 检查是否是有效的zip文件
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            return any('content.json' in f for f in file_list) or any('content.xml' in f for f in file_list)
    except Exception:
        return False


def format_error(error, file_name=""):
    """格式化错误信息并提供解决建议"""
    error_text = str(error)
    suggestions = {
        "源文件不存在": "请确认文件存放在正确的位置",
        "没有读取源文件的权限": "请检查文件权限，确保有读取权限",
        "没有写入输出目录的权限": "请检查输出目录权限，确保有写入权限",
        "文件过小": "文件可能不是有效的XMind文件，请检查文件完整性",
        "无效的XMind文件格式": "文件可能已损坏或不是XMind文件，请使用XMind软件检查文件",
        "无法识别的XMind文件结构": "XMind文件格式可能不兼容，尝试用最新版XMind软件保存",
        "内存不足": "关闭其他应用程序释放内存，或者分批次处理大文件",
        "Bad zip file": "无效的XMind文件格式(不是有效的zip文件)",
        "No such file or directory": "找不到文件或目录",
        "Permission denied": "权限被拒绝"
    }
    
    # 格式化错误消息
    message = f"失败: {file_name}\n      错误原因: {error_text}"
    
    # 添加建议
    for key, suggestion in suggestions.items():
        if key in error_text:
            message += f"\n      解决建议: {suggestion}"
            return message
    
    # 默认建议
    message += "\n      解决建议: 请尝试重新运行程序，如果问题持续存在，请考虑重新创建XMind文件"
    return message


def convert_folder(folder_path, output_folder=None, max_workers=4, recursive=False, indent_style="  ", image_dir=None, backup_original=False):
    """转换文件夹中的所有XMind文件为Markdown"""
    if not os.path.isdir(folder_path):
        raise ValueError(f"错误: '{folder_path}' 不是一个有效的文件夹")
    
    # 创建必要的目录
    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    if output_folder and not image_dir:
        image_dir = os.path.join(output_folder, 'images')
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
    
    # 查找并验证XMind文件
    pattern = os.path.join(folder_path, "**" if recursive else "", "*.xmind")
    xmind_files = glob.glob(pattern, recursive=recursive)
    validated_files = [f for f in xmind_files if is_valid_xmind_file(f)]
    
    # 处理无效或缺失文件的情况
    if not xmind_files:
        print(f"在 '{folder_path}' 中未找到XMind文件")
        print(f"请将XMind文件放入 '{os.path.abspath(folder_path)}' 文件夹中")
        return (0, 0, 0)
    
    invalid_count = len(xmind_files) - len(validated_files)
    if invalid_count > 0:
        print(f"警告: 发现 {invalid_count} 个无效的XMind文件，已跳过")
    
    if not validated_files:
        print(f"无有效的XMind文件可转换，请检查文件格式或使用最新版XMind保存")
        return (0, invalid_count, len(xmind_files))
    
    # 显示进度函数
    def show_progress(completed, total, success, failed):
        progress = int((completed / total) * 100)
        progress_bar = "=" * int(progress / 2) + ">" + " " * (50 - int(progress / 2))
        sys.stdout.write(f"\r转换进度: [{progress_bar}] {progress}% | 成功: {success} | 失败: {failed}")
        sys.stdout.flush()
    
    # 转换单个文件函数
    def convert_single_file(xmind_file):
        base_name = os.path.basename(xmind_file)
        try:
            # 确定输出路径
            if output_folder:
                md_filename = os.path.splitext(base_name)[0] + ".md"
                output_file = os.path.join(output_folder, md_filename)
                file_image_dir = image_dir if image_dir else os.path.join(
                    output_folder, 'images', os.path.splitext(base_name)[0]
                )
                if not os.path.exists(file_image_dir):
                    os.makedirs(file_image_dir)
            else:
                output_file = None
                file_image_dir = None
            
            # 转换文件
            converter = XMindToMarkdown(
                xmind_file, 
                indent_style=indent_style, 
                image_dir=file_image_dir,
                backup_original=backup_original
            )
            result_path, markdown_content = converter.save_markdown(output_file)
            
            # 返回成功结果
            backup_info = f"，备份于 {converter.backup_file}" if backup_original and converter.backup_file else ""
            return (xmind_file, True, None, result_path, backup_info)
        except Exception as e:
            return (xmind_file, False, str(e), None, "")
    
    # 并行处理文件
    total_files = len(validated_files)
    print(f"找到 {total_files} 个有效的XMind文件")
    
    success_count = 0
    failed_count = 0
    completed_count = 0
    failed_files = []
    
    show_progress(0, total_files, 0, 0)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(convert_single_file, file): file for file in validated_files}
        
        for future in as_completed(futures):
            xmind_file, success, error, output_path, backup_info = future.result()
            completed_count += 1
            
            if success:
                success_count += 1
                print(f"\n成功: {os.path.basename(xmind_file)} -> {output_path}")
                print(f"      原始文件保留在 {os.path.dirname(xmind_file)} 目录{backup_info}")
            else:
                failed_count += 1
                failed_files.append((xmind_file, error))
                print(f"\n{format_error(error, os.path.basename(xmind_file))}")
            
            show_progress(completed_count, total_files, success_count, failed_count)
    
    # 显示结果摘要
    print(f"\n\n转换完成: 总计 {total_files} 个文件, 成功 {success_count} 个, 失败 {failed_count} 个")
    print(f"所有原始XMind文件仍保留在 {os.path.abspath(folder_path)} 目录中")
    
    # 如果有失败文件，提供简洁的解决建议
    if failed_files:
        print("\n失败文件汇总及可能解决方法:")
        for i, (failed_file, error) in enumerate(failed_files, 1):
            print(f"  {i}. {os.path.basename(failed_file)}")
        
        print("\n常见解决方法:")
        print("  • 使用最新版XMind软件重新保存文件")
        print("  • 检查文件读写权限和文件名特殊字符")
        print("  • 对于大文件，尝试关闭其他应用释放内存")
    
    return (success_count, failed_count, total_files)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将XMind思维导图转换为Markdown格式')
    
    # 设置子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 单文件转换命令
    file_parser = subparsers.add_parser('file', help='转换单个XMind文件')
    file_parser.add_argument('input', help='输入的XMind文件路径')
    file_parser.add_argument('-o', '--output', help='输出的Markdown文件路径')
    file_parser.add_argument('--indent', default='  ', help='Markdown列表缩进样式 (默认: 两个空格)')
    file_parser.add_argument('--image-dir', help='指定图片保存目录')
    file_parser.add_argument('--backup', action='store_true', help='创建原始XMind文件的备份')
    
    # 文件夹转换命令
    folder_parser = subparsers.add_parser('folder', help='转换文件夹中的所有XMind文件')
    folder_parser.add_argument('input', nargs='?', default='XMIND', help='输入文件夹路径 (默认: XMIND)')
    folder_parser.add_argument('-o', '--output', help='输出文件夹路径 (默认: 与输入文件相同位置)')
    folder_parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子文件夹')
    folder_parser.add_argument('-j', '--jobs', type=int, default=4, help='同时处理的最大文件数 (默认: 4)')
    folder_parser.add_argument('--indent', default='  ', help='Markdown列表缩进样式 (默认: 两个空格)')
    folder_parser.add_argument('--image-dir', help='指定图片保存的总目录')
    folder_parser.add_argument('--backup', action='store_true', help='创建原始XMind文件的备份')
    
    # 兼容旧版本的命令行参数
    parser.add_argument('--folder', help='[已弃用] 使用 "folder" 命令替代')
    parser.add_argument('--file', help='[已弃用] 使用 "file" 命令替代')
    parser.add_argument('xmind_file', nargs='?', help='[已弃用] 使用 "file" 命令替代')
    parser.add_argument('md_file', nargs='?', help='[已弃用] 使用 "file" 命令替代')
    
    args = parser.parse_args()
    
    # 处理旧版本兼容性
    if args.folder:
        print("[警告] --folder 参数已弃用，请使用 'folder' 命令替代")
        args.command = 'folder'
        args.input = args.folder
        args.output = None
        args.recursive = False
        args.jobs = 4
        args.indent = '  '
        args.image_dir = None
        args.backup = False
    elif args.file:
        print("[警告] --file 参数已弃用，请使用 'file' 命令替代")
        args.command = 'file'
        args.input = args.file
        args.output = None
        args.indent = '  '
        args.image_dir = None
        args.backup = False
    elif args.xmind_file:
        print("[警告] 直接传递文件参数的方式已弃用，请使用 'file' 命令替代")
        args.command = 'file'
        args.input = args.xmind_file
        args.output = args.md_file
        args.indent = '  '
        args.image_dir = None
        args.backup = False
    
    try:
        # 默认执行批量转换
        if not args.command:
            print("=" * 60)
            print("XMind 批量转换工具")
            print("=" * 60)
            print("将从XMIND文件夹中读取XMind文件并转换为Markdown格式")
            print("生成的Markdown文件将保存到get_markdown文件夹中")
            print("-" * 60)
            
            args.command = 'folder'
            args.input = 'XMIND'
            args.output = 'get_markdown'
            args.recursive = False
            args.jobs = 4
            args.indent = '  '
            args.image_dir = None
            args.backup = False
        
        # 处理命令
        if args.command == 'file':
            # 检查文件存在
            if not os.path.exists(args.input):
                print(f"错误: 文件 '{args.input}' 不存在")
                return 1
            
            # 转换单个文件
            converter = XMindToMarkdown(
                args.input,
                indent_style=args.indent,
                image_dir=args.image_dir,
                backup_original=args.backup
            )
            output_path, markdown_content = converter.save_markdown(args.output)
            print(f"已保存到: {output_path}")
            print(f"图片保存在: {converter.image_dir}")
            print("原始XMind文件已保留" + (f"，备份于: {converter.backup_file}" if args.backup else ""))
            return 0
            
        elif args.command == 'folder':
            input_folder = args.input
            output_folder = args.output
            
            # 创建或检查XMIND文件夹
            if not os.path.exists(input_folder):
                os.makedirs(input_folder)
                print(f"已创建 '{input_folder}' 文件夹，请放入XMind文件后再次运行")
                print(f"文件夹位置: {os.path.abspath(input_folder)}")
                return 0
            
            # 检查文件夹是否有XMind文件
            has_xmind = any(f.lower().endswith('.xmind') for f in os.listdir(input_folder))
            if not has_xmind:
                print(f"警告: '{input_folder}' 文件夹中没有XMind文件")
                print(f"请将XMind文件放入 '{os.path.abspath(input_folder)}' 后再次运行")
                return 0
            
            # 创建输出文件夹
            if output_folder and not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # 执行转换
            start_time = time.time()
            success_count, failed_count, total_files = convert_folder(
                input_folder,
                output_folder,
                args.jobs,
                args.recursive,
                args.indent,
                args.image_dir,
                args.backup
            )
            end_time = time.time()
            
            print(f"总耗时: {end_time - start_time:.2f} 秒")
            
            # 检查源文件完整性
            if success_count > 0:
                xmind_files = glob.glob(os.path.join(input_folder, "*.xmind"))
                if all(os.path.exists(f) for f in xmind_files):
                    print(f"所有源文件仍保留在 {input_folder} 中")
            
            return 0 if failed_count == 0 else 1
            
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 