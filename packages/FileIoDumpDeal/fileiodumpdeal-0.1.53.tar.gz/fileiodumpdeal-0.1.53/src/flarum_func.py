# -*- coding: utf-8 -*-
"""
 __createTime__ = 20250605-111924
 __author__ = "WeiYanfeng"
 __version__ = "0.0.1"

~~~~~~~~~~~~~~~~~~~~~~~~
程序单元功能描述
封装Flarum所需的独立函数
~~~~~~~~~~~~~~~~~~~~~~~~
# 依赖包 Package required
# pip install weberFuncs

"""
import sys
from weberFuncs import PrintTimeMsg
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []  # 存储文本片段

    def handle_data(self, data):
        # 重写基类函数
        self.text_parts.append(data)  # 捕获非标签内容

    def get_clean_text(self):
        return ''.join(self.text_parts)  # 合并所有文本


def get_clean_text_from_html(sHtml):
    # 剔除HTML标签
    parser = TextExtractor()
    parser.feed(sHtml)
    return parser.get_clean_text()


def strip_mention_content(sContent):
    # 剔除提到用户名信息分别返回
    # @信息仅出现内容开头和结尾，用户名不超过32字符
    # sV=@RobotAI1 @RobotAI2 Content @RobotAI9
    # 返回 ['RobotAI1', 'RobotAI2', 'RobotAI9'] 和 'Content'
    MAX_NAME_LEN = 32 + 1
    listAt = []
    sV = sContent.strip()
    while sV:  # 剔除开头的@
        if not sV.startswith('@'): break
        iSpace = sV.find(' ')
        if not (0 < iSpace <= MAX_NAME_LEN): break
        sAt = sV[1:iSpace]
        if sAt:
            listAt.append(sAt)
        sV = sV[iSpace + 1:].strip()

    while sV:  # 剔除结尾的@
        iAt = sV.rfind('@', -MAX_NAME_LEN)
        if iAt < 0: break  # return -1 if not found
        sAt = sV[iAt + 1:]
        if ' ' in sAt: break  # 名字中不能有空格
        if sAt:
            listAt.append(sAt)
        sV = sV[:iAt].strip()

    PrintTimeMsg(f'strip_mention_content({sContent})={listAt},sV={sV}=')
    return listAt, sV


def get_from_dict_default(dictValue, sDotKey):
    # 根据 k1.k2.k3 从dict中取得相应值
    dictV = dictValue
    for sK in sDotKey.split('.'):
        dictV = dictV.get(sK, {})
        if not isinstance(dictV, dict):  # 不是dict，则跳出
            break
    return dictV


def mainClassOne():
    # strip_mention_content('@RobotAI1 @RobotAI2 Content @RobotAI9')
    # strip_mention_content('@Robot @AI1 @RobotAI2 @RobotAI3@ Content @RobotAI901234567890 你你你哈哈哈')
    # strip_mention_content('改为七言古诗 @RobotAI @RobotDeepSeek70b')
    strip_mention_content('给出冒泡、快速、堆排序算法的python代码 @RobotWebKimi @RobotWebYuanbao')
    pass


if __name__ == '__main__':
    mainClassOne()
