# -*- coding: utf-8 -*-
"""
 __createTime__ = 20250605-105856
 __author__ = "WeiYanfeng"
 __version__ = "0.0.1"

~~~~~~~~~~~~~~~~~~~~~~~~
程序单元功能描述
封装 Flarum API
直接面向应用
~~~~~~~~~~~~~~~~~~~~~~~~
# 依赖包 Package required
# pip install weberFuncs

"""
import sys

from weberFuncs import PrintTimeMsg
from weberFuncs import PrettyPrintStr
import os
import json
from CFlarumJson import CFlarumJson
from flarum_func import get_clean_text_from_html, get_from_dict_default


class CFlarumOper(CFlarumJson):
    # 封装Flarum API 基类，到需要明确 UrlPath 的级别

    def __init__(self, sWorkDir=''):
        super().__init__(sWorkDir)

    def page_get_all_debug(self):
        # page_get_all 系列函数调试
        lsReturn = []

        def _cbHandleDebug(oJson):
            lsReturn.append(oJson)
            return True

        sDiscussionId = '14'
        sUrl = self.api_posts(f'?filter[discussion]={sDiscussionId}')  # 可以取到完整回帖信息

        sTagSlug = 'TaskEveryDay'
        sUrl = self.api_discussions(f'?filter[tag]={sTagSlug}')  # 可以取到完整话题信息

        sUrl = self.api_notifications()  # 可以取到完整通知信息
        self.page_get_call(sUrl, _cbHandleDebug)
        self.debug_json_print_object(lsReturn, r'E:\tmp\page_get_all_debug.json')

    # def get_discussion_dict_by_tag(self, sFocusTag):
    #     # 根据关注标签，获取讨论话题的标识和标题字典
    #     # WeiYF.20250512 经测试，无法按tagid进行过滤，只能按tag的slug过滤
    #     sParam = f'?filter[tag]={sFocusTag}'
    #     oJson = self._get_discussions(sParam)
    #     dictTitleByDiscussionId = {}
    #     if oJson:
    #         for post in oJson['data']:
    #             sId = post['id']
    #             dictAttr = post['attributes']
    #             dictTitleByDiscussionId[sId] = dictAttr['title']
    #     PrintTimeMsg(f"get_discussion_dict_by_tag({sFocusTag}).dictTitleByDiscussionId={PrettyPrintStr(dictTitleByDiscussionId)}")
    #     return dictTitleByDiscussionId

    def page_get_all_discussions_by_tag_slug(self, sTagSlug):
        # 根据关注标签 sTagSlug，获取全部讨论话题的标识和标题字典
        # WeiYF.20250512 经测试，无法按tagid进行过滤，只能按tag的slug过滤
        dictTitleByDiscussionId = {}

        def _cbHandleDiscussions(oJson):
            if oJson and 'data' in oJson:
                for post in oJson.get('data', []):
                    if post['type'] == 'discussions':
                        dictTitleByDiscussionId[post['id']] = get_from_dict_default(post, 'attributes.title')
                return True
            return False

        sUrl = self.api_discussions(f'?filter[tag]={sTagSlug}')  # 可以取到完整话题信息
        self.page_get_call(sUrl, _cbHandleDiscussions)

        if self.bDebugPrint:
            for sId, sTitle in dictTitleByDiscussionId.items():
                PrintTimeMsg(f"page_get_all_posts_by_discussion_id({sId}).sTitle={sTitle[:20]}=")
        return dictTitleByDiscussionId

    def page_get_all_posts_by_discussion_id(self, sDiscussionId):
        # 通过 discussion_id 获取全部回帖
        dictPosts = {}
        dictUserName = {}

        # sUrl = self.api_discussions(f'/{sDiscussionId}')
        # 该URL存在返回 included 数据包含的回帖不全，但 data.relationships 中是全的

        def _cbHandlePosts(oJson):
            if oJson and 'data' in oJson:
                for post in oJson.get('data', []):
                    if post['type'] == 'posts':
                        sContent = get_from_dict_default(post, 'attributes.content')
                        if not sContent:
                            sContent = get_from_dict_default(post, 'attributes.contentHtml')
                            sContent = get_clean_text_from_html(sContent)
                        dictPosts[post['id']] = {
                            'sContent': sContent,
                            'createdAt': get_from_dict_default(post, 'attributes.createdAt'),
                            'user_id': get_from_dict_default(post, 'relationships.user.data.id'),
                        }
                for post in oJson.get('included', []):
                    if post['type'] == 'users':
                        dictUserName[post['id']] = get_from_dict_default(post, 'attributes.displayName')
                return True
            return False

        sUrl = self.api_posts(f'?filter[discussion]={sDiscussionId}')  # 可以取到完整回帖信息
        self.page_get_call(sUrl, _cbHandlePosts)
        # self.debug_json_print_object(lsReturn, r'E:\tmp\page_get_all_posts_by_discussion_id.json')
        for dictV in dictPosts.values():
            if 'user_id' in dictV:
                # 合并 sUserName 到 dictReplyInfo
                user_id = dictV['user_id']
                sUserName = dictUserName.get(user_id, user_id)
                dictV['sUserName'] = sUserName
        if self.bDebugPrint:
            for sId, dictV in dictPosts.items():
                sContent = dictV.get('sContent', '')
                PrintTimeMsg(f"page_get_all_posts_by_discussion_id({sId}).sContent={sContent[:20]}=")
        return dictPosts

    def get_topic_by_discussion_id(self, sDiscussionId):
        # 根据讨论话题标识，获取话题的内容
        oJson = self._get_call(self.api_discussions(f'/{sDiscussionId}'))
        sContent = ''
        if oJson and 'data' in oJson:
            # post = oJson.get('data', {})
            # if post['type'] == 'discussions':
            #     pass
            for post in oJson.get('included', []):
                if post['type'] == 'posts':
                    sContent = get_from_dict_default(post, 'attributes.content')
                    if not sContent:
                        sContent = get_from_dict_default(post, 'attributes.contentHtml')
                        sContent = get_clean_text_from_html(sContent)
                    break  # First 仅取第一个
        if self.bDebugPrint:
            PrintTimeMsg(f"get_topic_by_discussion_id({sDiscussionId}).sContent={sContent}=")
        return sContent

    def page_get_all_self_notifications(self):
        # 获取当前用户全部通知信息
        dictNotiInfo = {}
        dictPostInfo = {}

        def _cbHandleNotifications(oJson):
            if oJson and 'data' in oJson:
                for post in oJson.get('data', []):
                    if post['type'] == 'notifications':
                        isRead = get_from_dict_default(post, 'attributes.isRead')
                        if isRead: continue
                        dictNotiInfo[post['id']] = {
                            # 'createdAt': get_from_dict_default(post, 'attributes.createdAt'),
                            # 'contentType': get_from_dict_default(post, 'attributes.contentType'),
                            # 'user_id': get_from_dict_default(post, 'relationships.fromUser.data.id'),
                            'post_id': get_from_dict_default(post, 'relationships.subject.data.id'),
                        }
                for post in oJson.get('included', []):
                    if post['type'] == 'posts':
                        dictPostInfo[post['id']] = {
                            'discussion_id': get_from_dict_default(post, 'relationships.discussion.data.id'),
                        }
                return True
            return False

        sUrl = self.api_notifications()  # 可以取到完整通知信息
        self.page_get_call(sUrl, _cbHandleNotifications)
        # self.debug_json_print_object(lsReturn, r'E:\tmp\page_get_all_self_notifications.json')
        for dictV in dictNotiInfo.values():
            # 合并 dictPostInfo 到 dictNotiInfo
            post_id = dictV['post_id']
            dictP = dictPostInfo.get(post_id, {})
            dictV.update(dictP)

        if self.bDebugPrint:
            for sId, dictV in dictNotiInfo.items():
                # discussion_id = dictV.get('discussion_id', '')
                PrintTimeMsg(f"page_get_all_self_notifications({sId}).dictV={dictV}=")
        return dictNotiInfo

    def gen_chat_dict_by_disc_post_id(self, sDiscussionId, sPostId):
        # 通过 sDiscussionId, sPostId 生成聊天字典列表
        # dictReplyInfo = self.get_reply_dict_by_discussion_id(sDiscussionId)
        # return self.gen_chat_list_from_reply(dictReplyInfo, sPostId)
        dictPosts = self.page_get_all_posts_by_discussion_id(sDiscussionId)

        iPostId = int(sPostId)
        listDictChat = []
        for post_id, dictPost in dictPosts.items():
            iId = int(post_id)
            if iId < iPostId:
                listDictChat.append(dictPost)
            elif iId == iPostId:
                sContentLast = dictPost.get('sContent', '')
                sContentLast = sContentLast.strip()
                if sContentLast.startswith('@'):  # 以@开头，则表示是新任务，不需要之前的交互历史
                    listDictChat = []
                listDictChat.append(dictPost)

        if self.bDebugPrint:
            PrintTimeMsg(f"gen_chat_list_from_reply().listDictChat={PrettyPrintStr(listDictChat)}")
        return listDictChat


def mainCFlarumOper():
    sWorkDir = r'E:\WeberSrcRoot\Rocky9GogsRoot\RobotAgentMCP\FileIoDumpDeal'
    o = CFlarumOper(sWorkDir)
    # o.page_get_all_debug()
    # o.page_get_all_discussions_by_tag_slug('TaskEveryDay')
    # o.page_get_all_posts_by_discussion_id('14')
    # o.get_topic_by_discussion_id('13')
    # o.page_get_all_self_notifications()
    o.gen_chat_dict_by_disc_post_id('14', '208')



if __name__ == '__main__':
    mainCFlarumOper()
