# -*- coding: utf-8 -*-
"""
 __createTime__ = 20250605-105856
 __author__ = "WeiYanfeng"
 __version__ = "0.0.1"

~~~~~~~~~~~~~~~~~~~~~~~~
程序单元功能描述
封装 Flarum API
[Discussion 讨论](https://justjavac.gitbooks.io/flarum/content/using/api.html)
从 flarum_api 改造而来，分层次拆分多个类
~~~~~~~~~~~~~~~~~~~~~~~~
# 依赖包 Package required
# pip install weberFuncs

"""
import sys

from weberFuncs import PrintTimeMsg, PrintAndSleep
from weberFuncs import PrettyPrintStr
import os
import json
import requests
from dotenv import load_dotenv


class CFlarumBase:
    # 封装Flarum API 基类，到需要明确 UrlPath 的级别

    def __init__(self, sWorkDir=''):
        # sWorkDir 是工作目录，其下的 flarum.env 文件就是环境变量参数文件
        if sWorkDir:
            self.sWorkDir = sWorkDir
        else:
            self.sWorkDir = os.getcwd()
        PrintTimeMsg(f'CFlarumBase.sWorkDir={self.sWorkDir}=')
        # self.oControlCron = control_cron(self.sWorkDir)

        # sEnvDir = GetSrcParentPath(__file__, True)
        sEnvFN = os.path.join(self.sWorkDir, 'flarum.env')
        # sEnvFN = os.path.join(self.sWorkDir, 'flarumBrain.env')
        bLoad = load_dotenv(dotenv_path=sEnvFN)  # load environment variables from .env
        PrintTimeMsg(f"CFlarumBase.load_dotenv({sEnvFN})={bLoad}")
        if not bLoad:
            exit(-1)

        self.sFlarumUrl = os.getenv("FLARUM_URL")
        self.sFlarumToken = os.getenv("FLARUM_TOKEN")

        self.bDebugPrint = True  # 控制是否打印日志

    def get_env_param(self, sEnvKey):
        # 从环境变量中读取参数，以便项目共享
        return os.getenv(sEnvKey)

    def debug_json_print_object(self, oJson, sDebugFN):
        # 格式化输出json数据到调试文件，仅在
        if not self.bDebugPrint:
            return
        with open(sDebugFN, 'w', encoding='utf8') as f:
            sOut = json.dumps(oJson, indent=4)
            f.write(sOut)

    def _post_call(self, sUrlPath, dictPayload, sMethodOverride=''):
        # 向Flarum发送 POST 请求， sUrlPath = /api/discussions
        # dictPayload 提交的数据
        # sMethodOverride 添加 x-http-method-override 的方法，默认为空不添加
        #   添加 x-http-method-override = PATCH 以模拟 PATCH 方法
        sUrl = f'{self.sFlarumUrl}{sUrlPath}'
        PrintTimeMsg(f'_post_call.sUrl={sUrl}={sMethodOverride}=')
        dictHeaders = {
            "Authorization": f"Token {self.sFlarumToken}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }
        if sMethodOverride:
            dictHeaders['x-http-method-override'] = sMethodOverride  # 'PATCH'
        try:
            response = requests.post(sUrl, headers=dictHeaders, json=dictPayload)
            if response.status_code in [201, 200]:
                PrintTimeMsg(f"_post_call.ok:len(response.text)={len(response.text)}={response.status_code}=")
                oJson = response.json()
                if self.bDebugPrint:
                    PrintTimeMsg(f"_post_call.oJson={PrettyPrintStr(oJson)}")
                return oJson
            else:
                PrintTimeMsg(f"_post_call.error:status_code={response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            PrintTimeMsg(f"_post_call.e={str(e)}=")
        return None

    def _get_call(self, sUrlPath):
        # 向Flarum发送 GET 请求， sUrlPath = /api/discussions
        sUrl = sUrlPath
        if sUrlPath.startswith('/'):
            sUrl = f'{self.sFlarumUrl}{sUrlPath}'
        PrintTimeMsg(f'_get_call.sUrl={sUrl}=')
        dictHeaders = {
            "Authorization": f"Token {self.sFlarumToken}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }
        try:
            response = requests.get(sUrl, headers=dictHeaders)
            if response.status_code in [201, 200]:
                PrintTimeMsg(f"_get_call.ok:len(response.text)={len(response.text)}={response.status_code}=")
                oJson = response.json()
                if self.bDebugPrint:
                    # PrintTimeMsg(f"_get_call.oJson={PrettyPrintStr(oJson)[:900]}")
                    PrintTimeMsg(f"_get_call.oJson={str(oJson)[:]}")
                return oJson
            else:
                PrintTimeMsg(f"_get_call.error:status_code={response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            PrintTimeMsg(f"_get_call({sUrl}).e={str(e)}=")
        return None

    def _page_get_call(self, sUrlPath, callbackHandle):
        # 翻页调用 get 方法，并采用返回结果传给 callbackHandle 函数
        iCallCnt = 0
        while True:
            oJson = self._get_call(sUrlPath)
            if not oJson:
                return 'oJson=Null'
            bRet = callbackHandle(oJson)
            if not bRet:
                return 'callback=Break'
            dictLinks = oJson.get('links', {})
            sUrlNext = dictLinks.get('next', '')
            if not sUrlNext:
                return 'NoNext'
            sUrlPath = sUrlNext
            iCallCnt += 1
            PrintAndSleep(1, f'page_get_call.iCallCnt={iCallCnt}=')

    def page_get_call(self, sUrlPath, callbackHandle):
        sRetMsg = self._page_get_call(sUrlPath, callbackHandle)
        PrintTimeMsg(f"page_get_call({sUrlPath}).sRetMsg={sRetMsg}=")

    def api_tags(self, sParam=''):
        # 生成 /api/tags - 标签
        return f'/api/tags{sParam}'

    def api_discussions(self, sParam=''):
        # 生成 /api/discussions - 获取并过滤讨论话题
        return f'/api/discussions{sParam}'

    def api_posts(self, sParam=''):
        # 生成 /api/posts - 获取并过滤回帖
        return f'/api/posts{sParam}'

    def api_notifications(self, sParam=''):
        # 调用 /api/notifications - 通知消息
        return f'/api/notifications{sParam}'




def mainCFlarumBase():
    sWorkDir = r'E:\WeberSrcRoot\Rocky9GogsRoot\RobotAgentMCP\FileIoDumpDeal'
    o = CFlarumBase(sWorkDir)
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
    # o.get_reply_dict_by_discussion_id('13')
    # o.get_title_topic_by_discussion_id('13')
    # o.get_self_notifications()
    # dictReplyInfo = o.get_reply_dict_by_discussion_id('13')
    # dictReplyInfo = o.get_reply_dict_by_discussion_id('14')
    # o.gen_chat_list_from_reply(dictReplyInfo, '187')
    # o.get_posts_dict_by_discussion_id('14')
    # o._get_call(o.api_posts('/208'))
    o._get_call(o.api_discussions('/13'))


if __name__ == '__main__':
    mainCFlarumBase()

