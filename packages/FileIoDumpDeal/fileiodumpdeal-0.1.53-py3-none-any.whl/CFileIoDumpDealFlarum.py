# -*- coding: utf-8 -*-
"""
 __createTime__ = 20250507-143900
 __author__ = "WeiYanfeng"
 __version__ = "0.0.1"

~~~~~~~~~~~~~~~~~~~~~~~~
程序单元功能描述
Program description
~~~~~~~~~~~~~~~~~~~~~~~~
# 依赖包 Package required
# pip install weberFuncs

"""
import sys
from weberFuncs import PrintTimeMsg, GetCurrentTime
from weberFuncs import GetYYYYMMDDhhnnss
from CFileIoDumpDealBase import CFileIoDumpDealBase
# from flarum_api import flarum_api
from CFlarumOper import CFlarumOper
import os
import json
from calc_match_time import calc_match_time
from control_cron import control_cron
from flarum_func import strip_mention_content


class CFileIoDumpDealFlarum(CFileIoDumpDealBase):
    def __init__(self, sMcpTaskDir, sFlarumWorkDir):
        # sMcpTaskDir 是对应 TaskMcpClient 的Task工作目录，带尾部task
        # sFlarumWorkDir flarum_api对应工作目录，用于加载 flarum.env 等
        # CFileIoDumpDealBase.__init__(self, sMcpTaskDir)
        super().__init__(sMcpTaskDir)
        if not sFlarumWorkDir:
            # sFlarumWorkDir = GetSrcParentPath(__file__, True)
            sFlarumWorkDir = os.getcwd()
        self.oFlarum = CFlarumOper(sFlarumWorkDir)
        self.oFlarum.bDebugPrint = False
        self.sFlarumTagFocus = self.oFlarum.get_env_param('FLARUM_TAG_FOCUS')
        self.sCronParamDefault = self.oFlarum.get_env_param('CRON_PARAM_DEFAULT')
        self.sRobotNameId = self.oFlarum.get_env_param('ROBOT_NAME_ID')

        self.oControlCron = control_cron(sFlarumWorkDir)

    def DumpFile4Query(self, sQueryDir):
        # 导出到文件到 sQueryDir 目录，作为 TaskMcpClient 的Query输入
        # 返回导出文件数目
        # 重写基类同名函数
        # PrintTimeMsg(f'CFileIoDumpDealFlarum.DumpFile4Query.sQueryDir={sQueryDir}=')
        # iDumpCnt = self.oFlarum.dump_file_4_query_discussion(sQueryDir)
        iDumpCnt = 0
        sTmNextCheck = GetYYYYMMDDhhnnss(60 * 60 * 24)  # 默认值
        dictTitleByDiscussionId = self.oFlarum.page_get_all_discussions_by_tag_slug(self.sFlarumTagFocus)
        for sDiscussionId, sTitle in dictTitleByDiscussionId.items():
            sCcid = f'discussion_%s' % sDiscussionId
            sAtEvery = self.oControlCron.get_control_cron_param(sCcid, sTitle)
            if not sAtEvery:
                sAtEvery = self.sCronParamDefault
            sTmMatch, sTmCheck = calc_match_time(sAtEvery)
            if sTmNextCheck > sTmCheck:
                sTmNextCheck = sTmCheck
            dictTimeLog = self.oControlCron.load_control_cron_log(sCcid)
            if sTmMatch in dictTimeLog:
                sDumpInfo = dictTimeLog[sTmMatch]
                PrintTimeMsg(f"DumpFile4Query({sCcid}={sTmMatch})={sDumpInfo}=Pass!")
            else:
                # dictTitleTopic = self.oFlarum.get_title_topic_by_discussion_id(sDiscussionId)
                # sContent = dictTitleTopic.get('sContent', '')
                sContent = self.oFlarum.get_topic_by_discussion_id(sDiscussionId)
                if not sContent: continue
                sGenTm = GetCurrentTime()  # 加上执行时间后缀，避免不同周期的任务文件被覆盖
                sFN = f'flarum_{sDiscussionId}_{sGenTm}.md'
                sFullFN = os.path.join(sQueryDir, sFN)
                with open(sFullFN, 'w', encoding='utf8') as f:
                    f.write('%s\n' % sContent)
                PrintTimeMsg(f"DumpFile4Query({sFullFN})=OK!")
                sDumpStatus = 'DumpOK'
                iDumpCnt += 1
                dictTimeLog[sTmMatch] = '%s@%s' % (sDumpStatus, GetCurrentTime())
                self.oControlCron.save_control_cron_log(sCcid, dictTimeLog)
        # PrintTimeMsg(f"DumpFile4Query().iDumpCnt={iDumpCnt}=")
        return iDumpCnt, sTmNextCheck

    def _arrange_gen_chat_dict(self, sDiscussionId, sPostId):
        # 整理转化聊天列表为字典，添加机器人标识等信息
        listDictChat = self.oFlarum.gen_chat_dict_by_disc_post_id(sDiscussionId, sPostId)
        if not listDictChat: return {}  # 列表为空，则返回{}
        listAtRobot = []
        for dictChat in listDictChat:
            sContent = dictChat.get('sContent', '')
            listAt, sV = strip_mention_content(sContent)
            listAtRobot.append(','.join(listAt))
            dictChat['sContent'] = sV  # 覆盖
        dictContent = {
            'sRobotNameId': self.sRobotNameId,
            'listAtRobot': listAtRobot,      # 从 listDictChat 中拆分出的 @ 信息列表
            'data': listDictChat,   # 专注于chat的聊天数据列表
        }
        return dictContent

    def NotiFile4Query(self, sQueryDir):
        # 导出通知消息文件到 sQueryDir 目录，作为 TaskMcpClient 的Query输入
        # 返回导出文件数目
        # 重写基类同名函数
        # PrintTimeMsg(f'CFileIoDumpDealFlarum.DumpFile4Query.sQueryDir={sQueryDir}=')
        # iDumpCnt = self.oFlarum.dump_file_4_query_discussion(sQueryDir)

        iDumpCnt = 0
        dictNotiInfo = self.oFlarum.page_get_all_self_notifications()
        for sNotificationId, dictInfo in dictNotiInfo.items():
            bDumpOk = False
            sDiscussionId = dictInfo.get('discussion_id', '')
            sPostId = dictInfo.get('post_id', '')
            if sDiscussionId and sPostId:
                dictContent = self._arrange_gen_chat_dict(sDiscussionId, sPostId)
                if dictContent:
                    sContent = json.dumps(dictContent, indent=4)
                    if sNotificationId and sDiscussionId and sContent:
                        sGenTm = GetCurrentTime()  # 加上执行时间后缀，避免不同周期的任务文件被覆盖
                        sFN = f'notify_{sDiscussionId}_{sGenTm}.md'
                        sFullFN = os.path.join(sQueryDir, sFN)
                        with open(sFullFN, 'w', encoding='utf8') as f:
                            f.write('%s\n' % sContent)
                        PrintTimeMsg(f"NotiFile4Query({sFullFN})=OK!")
                        self.oFlarum.mark_read_notification(sNotificationId)  # 标记为已读
                        iDumpCnt += 1
                        bDumpOk = True
            if not bDumpOk:
                PrintTimeMsg(f"NotiFile4Query({sNotificationId},{sDiscussionId},{sPostId})=ErrorToSkip!")
        # PrintTimeMsg(f"DumpFile4Query().iDumpCnt={iDumpCnt}=")
        return iDumpCnt

    def DealFileResult(self, sNoExtFN, sResultDir):
        # 将sResultDir目录下的回复文件，提交到其它系统，并移动到备份目录
        # sNoExtFN 不带扩展名及_R/_Q的文件名
        # 返回处理成功与否
        # 重写基类同名函数
        # PrintTimeMsg(f'CFileIoDumpDealFlarum.DumpFile4Query.sNoExtFN={sNoExtFN}={sResultDir}=')
        # bDealOk = self.oFlarum.deal_file_result_reply_to_discussion(sNoExtFN, sResultDir)
        bDealOk = False
        lsParam = sNoExtFN.split('_')
        if len(lsParam) >= 3:
            sDiscussionId = lsParam[1]
            # sGenTm = lsParam[2]
            sFN = f'{sNoExtFN}_R.md'
            sFullFN = os.path.join(sResultDir, sFN)
            with open(sFullFN, 'r', encoding='utf8') as f:
                sContent = f.read()
                oJson = self.oFlarum.reply_discussion_post(sDiscussionId, sContent)
                bDealOk = oJson is not None
            PrintTimeMsg(f"deal_file_result_reply_to_discussion({sNoExtFN})={bDealOk}")
            return bDealOk
        else:
            PrintTimeMsg(f"deal_file_result_reply_to_discussion().sNoExtFN={sNoExtFN}=FmtError!")
            return False
        # return bDealOk


def mainFileIoDumpDealFlarum():
    sTaskType = 'dump'  # dump/deal/notify
    # sTaskType = 'notify'
    sMcpTaskDir = r'E:\WeberSrcRoot\Rocky9GogsRoot\RobotAgentMCP\TaskMcpClient\task'
    # sFlarumWorkDir = r'E:\WeberSrcRoot\Rocky9GogsRoot\RobotAgentMCP\FileIoDumpDeal'
    sFlarumWorkDir = ''  # 默认为空，则取当前工作目录
    if len(sys.argv) >= 2:
        sTaskType = sys.argv[1]
        if len(sys.argv) >= 3:
            sMcpTaskDir = sys.argv[2]
            if len(sys.argv) >= 4:
                sFlarumWorkDir = sys.argv[3]
    else:
        # PrintTimeMsg('Usage: python CFileIoDumpDealFlarum.py <sMcpTaskDir> [<sFlarumWorkDir>]')
        PrintTimeMsg('Usage: DumpDealFlarum dump/deal/notify <sMcpTaskDir> [<sFlarumWorkDir>]')
        if not os.path.exists(sMcpTaskDir):
            sys.exit(-1)
    o = CFileIoDumpDealFlarum(sMcpTaskDir, sFlarumWorkDir)
    o.LoopFileIoDumpDeal(sTaskType)


if __name__ == '__main__':
    mainFileIoDumpDealFlarum()
