"""
Text to Markdown Converter

一个简单的文本文件转Markdown格式的工具
支持自动识别标题、段落、列表等常见文本结构
"""

import re
import os
from pathlib import Path
from typing import List, Optional, Union


class TextToMarkdownConverter:
    """文本到Markdown转换器"""

    def __init__(self):
        self.title_patterns = [
            # 匹配全大写的标题
            (r'^[A-Z\s\d]+$', 1),
            # 匹配以数字开头的标题 (如: 1. 标题, 1.1 标题)
            (r'^\d+\.?\d*\.?\s+.+', 2),
            # 匹配短行（可能是标题）
            (r'^.{1,50}$', 3),
        ]

    def detect_title_level(self, line: str) -> int:
        """
        检测行是否为标题，返回标题级别
        返回0表示不是标题，1-6表示标题级别
        """
        line = line.strip()
        if not line:
            return 0

        # 检查是否已经是markdown标题
        if line.startswith('#'):
            return 0

        # 检查各种标题模式
        for pattern, level in self.title_patterns:
            if re.match(pattern, line):
                # 全大写的短行可能是主标题
                if level == 1 and len(line) < 30:
                    return 1
                # 数字开头的可能是二级标题
                elif level == 2:
                    return 2
                # 短行可能是三级标题
                elif level == 3 and len(line) < 30:
                    return 3

        return 0

    def detect_list_item(self, line: str) -> bool:
        """检测是否为列表项"""
        line = line.strip()
        # 检查是否以 -, *, +, 数字. 开头
        list_patterns = [
            r'^[-*+]\s+',  # - item, * item, + item
            r'^\d+\.\s+',  # 1. item, 2. item
            r'^[a-zA-Z]\.\s+',  # a. item, A. item
        ]

        for pattern in list_patterns:
            if re.match(pattern, line):
                return True
        return False

    def convert_line(self, line: str, prev_line: str = "", next_line: str = "") -> str:
        """转换单行文本为markdown格式"""
        original_line = line
        line = line.strip()

        if not line:
            return "\n"

        # 检查是否为标题
        title_level = self.detect_title_level(line)
        if title_level > 0:
            return f"{'#' * title_level} {line}\n\n"

        # 检查是否为列表项
        if self.detect_list_item(line):
            # 如果不是以markdown列表格式开头，转换为markdown列表
            if not re.match(r'^[-*+]\s+', line):
                # 移除原有的列表标记
                line = re.sub(r'^(\d+\.|[a-zA-Z]\.|[-*+])\s*', '', line)
                return f"- {line}\n"
            return f"{line}\n"

        # 普通段落
        return f"{line}\n\n"

    def convert_text_to_markdown(self, text: str) -> str:
        """将文本转换为markdown格式"""
        lines = text.split('\n')
        markdown_lines = []

        for i, line in enumerate(lines):
            prev_line = lines[i-1] if i > 0 else ""
            next_line = lines[i+1] if i < len(lines)-1 else ""

            converted = self.convert_line(line, prev_line, next_line)
            markdown_lines.append(converted)

        # 清理多余的空行
        result = ''.join(markdown_lines)
        # 移除连续的空行，最多保留两个换行符
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip() + '\n'

    def convert_file(self, input_path: Union[str, Path],
                    output_path: Optional[Union[str, Path]] = None,
                    encoding: str = 'utf-8') -> str:
        """
        转换文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则自动生成
            encoding: 文件编码，默认utf-8

        Returns:
            输出文件路径
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")

        # 读取输入文件
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                text = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            encodings = ['gbk', 'gb2312', 'latin-1']
            for enc in encodings:
                try:
                    with open(input_path, 'r', encoding=enc) as f:
                        text = f.read()
                    print(f"使用编码 {enc} 成功读取文件")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("无法确定文件编码，请手动指定encoding参数")

        # 转换为markdown
        markdown_text = self.convert_text_to_markdown(text)

        # 确定输出路径
        if output_path is None:
            output_path = input_path.with_suffix('.md')
        else:
            output_path = Path(output_path)

        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        return str(output_path)


def convert_text_to_markdown(input_file: Union[str, Path],
                           output_file: Optional[Union[str, Path]] = None,
                           encoding: str = 'utf-8') -> str:
    """
    便捷函数：将文本文件转换为markdown格式

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果为None则自动生成
        encoding: 文件编码，默认utf-8

    Returns:
        输出文件路径

    Example:
        >>> convert_text_to_markdown('example.txt')
        'example.md'

        >>> convert_text_to_markdown('input.txt', 'output.md')
        'output.md'
    """
    converter = TextToMarkdownConverter()
    return converter.convert_file(input_file, output_file, encoding)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python tt_md.py <输入文件> [输出文件]")
        print("示例: python tt_md.py example.txt")
        print("示例: python tt_md.py input.txt output.md")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result_path = convert_text_to_markdown(input_file, output_file)
        print(f"转换完成！输出文件: {result_path}")
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)