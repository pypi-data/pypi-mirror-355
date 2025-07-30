import json
import os
import matplotlib.pyplot as plt


def set_chinese_font(font_name='SimHei'):
    """
    设置 matplotlib 使用支持中文的字体。
    
    参数:
        font_name (str): 字体名称，默认是 'SimHei'（黑体）。
                        可选如 'Microsoft YaHei'、'Arial Unicode MS' 等。
    """
    from matplotlib import rcParams
    rcParams['font.sans-serif'] = [font_name]
    rcParams['axes.unicode_minus'] = False
    print(f"已设置 matplotlib 字体为：{font_name}")

# 使用方式：
set_chinese_font()  # 或者 set_chinese_font('Microsoft YaHei')


def extract_notebook_text(ipynb_path, output_txt_path=None):
    """
    提取 Jupyter Notebook 文件中的所有 Markdown 和 Code cell 内容，
    并保存到指定或默认的文本文件中（默认是同名 .txt 文件）。
    
    参数：
        ipynb_path (str): 输入的 .ipynb 文件路径
        output_txt_path (str, optional): 输出的 .txt 文件路径。如果为 None，则使用与 ipynb 同名的 .txt 文件。
    """
    if output_txt_path is None:
        base_name = os.path.splitext(ipynb_path)[0]
        output_txt_path = base_name + '.txt'
    
    with open(ipynb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    with open(output_txt_path, 'w', encoding='utf-8') as out_file:
        for cell in notebook['cells']:
            if cell['cell_type'] in ['markdown', 'code']:
                content = ''.join(cell['source'])
                out_file.write(content + '\n\n')  # 添加空行作为分隔
