# -*- coding: utf-8 -*-
"""
 __createTime__ = 20250605-105856
 __author__ = "WeiYanfeng"
 __version__ = "0.0.1"

~~~~~~~~~~~~~~~~~~~~~~~~
程序单元功能描述
封装 Flarum API
[Discussion 讨论](https://justjavac.gitbooks.io/flarum/content/using/api.html)
~~~~~~~~~~~~~~~~~~~~~~~~
# 依赖包 Package required
# pip install weberFuncs

"""
import sys

from weberFuncs import PrintTimeMsg
from weberFuncs import PrettyPrintStr
import os
import json
from CFlarumBase import CFlarumBase


class CFlarumJson(CFlarumBase):
    # 封装Flarum API 基类，到需要明确 UrlPath 的级别

    def __init__(self, sWorkDir=''):
        # sWorkDir 是工作目录，其下的 flarum.env 文件就是环境变量参数文件
        super().__init__(sWorkDir)

        # TagId 与 Slug 映射关系
        self.dictTagIdByTagSlug = {}
        self.dictTagSlugByTagId = {}
        self.listTagNameSlug = []

    def _callbackSaveTagSlug(self, oJson):
        # 回调函数: 保存 tag id 和 slug 映射关系的
        if oJson and 'data' in oJson:
            for post in oJson['data']:
                sType = post['type']
                if sType != 'tags':
                    continue
                sId = post['id']
                dictAttr = post['attributes']
                sSlug = dictAttr['slug']
                sName = dictAttr['name']
                self.dictTagIdByTagSlug[sSlug] = sId
                self.dictTagSlugByTagId[sId] = sSlug
                self.listTagNameSlug.append((sId, sSlug, sName))
            return True
        return False

    def get_all_tags_dict_map(self):
        # 调用 GET /api/tags - 获取全部tag id 和 slug映射关系
        self.page_get_call(self.api_tags(), self._callbackSaveTagSlug)
        PrintTimeMsg(f"get_all_tags().listTagNameSlug={PrettyPrintStr(self.listTagNameSlug)}")

    def _create_new_discussion_by_tag_id(self, sTitle, sContent, sTagId):
        # 按某个标签Id创建新的讨论话题
        # 这里需要填入Tag标签ID，需要统一转为Slug
        dictPost = {
            "data": {
                "type": "discussions",
                "attributes": {
                    "title": sTitle,
                    "content": sContent
                },
                "relationships": {
                    "tags": {
                        "data": [
                            {
                                "type": "tags",
                                "id": sTagId
                            }
                        ]
                    }
                }
            }
        }
        return self._post_call(self.api_discussions(), dictPost)

    def create_new_discussion_by_tag_slug(self, sTitle, sContent, sTagSlug):
        # 按某个标签Id创建新的讨论话题
        if not self.dictTagIdByTagSlug:
            self.get_all_tags_dict_map()
        sTagId = self.dictTagIdByTagSlug.get(sTagSlug, '')
        if not sTagId:
            PrintTimeMsg(f"create_new_discussion_by_tag_slug.sTagSlug={sTagSlug}=NotExists!")
            return None
        return self._create_new_discussion_by_tag_id(sTitle, sContent, sTagId)

    def reply_discussion_post(self, sDiscussionId, sContent):
        # 针对某个讨论话题回帖
        dictPost = {
            "data": {
                "type": "posts",
                "attributes": {
                    "content": sContent
                },
                "relationships": {
                    "discussion": {
                        "data": {
                            "type": "discussions",
                            "id": sDiscussionId
                        }
                    }
                }
            }
        }
        return self._post_call(self.api_posts(), dictPost)

    def modify_post_by_post_id(self, sPostId, sContent):
        # 通过post_id修改某个讨论话题回帖
        dictPost = {
            "data": {
                "type": "posts",
                "attributes": {
                    "content": sContent
                },
                "id": sPostId
            }
        }
        return self._post_call(self.api_posts(f'/{sPostId}'), dictPost, 'PATCH')

    def modify_discussion_title_by_discussion_id(self, sDiscussionId, sTitle):
        # 通过discussion_id修改某个讨论话题标题
        dictPost = {
            "data": {
                "type": "discussions",
                "attributes": {
                    "title": sTitle
                },
                "id": sDiscussionId
            }
        }
        return self._post_call(self.api_discussions(f'/{sDiscussionId}'), dictPost, 'PATCH')

    def show_discussion_by_discussion_id(self, sDiscussionId):
        # 通过discussion_id恢复（显示）某个讨论话题
        return self._show_hide_discussion_by_discussion_id(sDiscussionId, False)

    def hide_discussion_by_discussion_id(self, sDiscussionId):
        # 通过discussion_id删除（隐藏）某个讨论话题
        return self._show_hide_discussion_by_discussion_id(sDiscussionId, True)

    def _show_hide_discussion_by_discussion_id(self, sDiscussionId, isHidden):
        # 通过discussion_id删除（隐藏）/恢复（显示）某个讨论话题
        dictPost = {
            "data": {
                "type": "discussions",
                "attributes": {
                    "isHidden": isHidden
                },
                "id": sDiscussionId
            }
        }
        return self._post_call(self.api_discussions(f'/{sDiscussionId}'), dictPost, 'PATCH')

    def _show_hide_post_by_post_id(self, sPostId, isHidden):
        # 通过post_id删除（隐藏）/恢复（显示）某个讨论话题回帖
        dictPost = {
            "data": {
                "type": "posts",
                "attributes": {
                    "isHidden": isHidden
                },
                "id": sPostId
            }
        }
        return self._post_call(self.api_posts(f'/{sPostId}'), dictPost, 'PATCH')

    def hide_post_by_post_id(self, sPostId):
        # 通过post_id删除（隐藏）某个讨论话题回帖
        return self._show_hide_post_by_post_id(sPostId, True)

    def show_post_by_post_id(self, sPostId):
        # 通过post_id恢复（显示）某个讨论话题回帖
        return self._show_hide_post_by_post_id(sPostId, False)

    def delete_post_by_post_id(self, sPostId):
        # 通过post_id永久删除某个讨论话题回帖
        # 列在此处，仅为展示该API的用法；实际并不需要该API
        dictPost = {}
        return self._post_call(self.api_posts(f'/{sPostId}'), dictPost, 'DELETE')

    def delete_discussion_by_discussion_id(self, sDiscussionId):
        # 通过discussion_id永久删除某个讨论话题
        # 列在此处，仅为展示该API的用法；实际并不需要该API
        dictPost = {}
        return self._post_call(self.api_discussions(f'/{sDiscussionId}'), dictPost, 'DELETE')

    def mark_read_notification(self, sNotificationId):
        # 通过sNotificationId标记某个通知已读
        dictPost = {
            "data": {
                "type": "notifications",
                "attributes": {
                    "isRead": True
                },
                "id": sNotificationId
            }
        }
        return self._post_call(self.api_notifications(f'/{sNotificationId}'), dictPost, 'PATCH')


def mainCFlarumJson():
    sWorkDir = r'E:\WeberSrcRoot\Rocky9GogsRoot\RobotAgentMCP\FileIoDumpDeal'
    o = CFlarumJson(sWorkDir)
    # o._get_discussions('?filter[tag]=general&sort&page[offset]=0')
    # o.get_discussion_dict_by_tag('general')
    # o.get_reply_dict_by_discussion_id('6')
    # o.get_title_topic_by_discussion_id('6')
    # o.modify_post_by_post_id('5', '测试程序自动发帖改贴mod.auto')
    # o.show_post_by_post_id('21')
    # o.delete_post_by_post_id('21')
    # o.get_reply_dict_by_discussion_id('6')
    # o.modify_discussion_title_by_discussion_id('13', 'test2.auto')
    # o.get_focus_discussion_dict()
    # sTestDir = r"E:\WeberSrcRoot\Rocky9GogsRoot\RobotAgentMCP\FileIoDumpDeal\run"
    # o.dump_file_4_query_discussion(sTestDir)
    # o.reply_discussion_post('6', 'main_flarum_api.auto.1')
    # o.modify_discussion_post('6', 'main_flarum_api.auto.1')
    # o.get_all_tags_dict_map()
    # o.create_new_discussion_by_tag_slug('测试发表新的话题', '测试发表新的内容api.1', 'general')
    # o.get_discussion_dict_by_tag('general')
    # o.get_discussion_dict_by_tag('1')
    # o._get_discussions('?filter[tagid]=2')  # 经测试，无法按tagid进行过滤
    # o.reply_discussion_post(20, 'main_flarum_api.auto.4 @admin')
    # o._get_discussion_posts('/163')
    # o._get_discussions('/13')
    # o.reply_discussion_post('13', '机器人回复1')
    o.get_all_tags_dict_map()



if __name__ == '__main__':
    mainCFlarumJson()
