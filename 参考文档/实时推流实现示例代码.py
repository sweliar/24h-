#!/usr/bin/env python
#coding=utf-8

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    body = dict()
    body['AppKey'] = '输入您在听悟管控台创建的Appkey'

    # 基本请求参数
    input = dict()

    #输入语音流格式和采样率和以下参数设置保持一致
    input['Format'] = 'pcm'
    input['SampleRate'] = 16000
    input['SourceLanguage'] = 'cn'
    input['TaskKey'] = 'task' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    input['ProgressiveCallbacksEnabled'] = False
    body['Input'] = input

    # AI相关参数，按需设置即可
    parameters = dict()

    # 音视频转换相关
    transcoding = dict()
    # 将原音视频文件转成mp3文件，用以后续浏览器播放
    # transcoding['TargetAudioFormat'] = 'mp3'
    # transcoding['SpectrumEnabled'] = False
    # parameters['Transcoding'] = transcoding

    # 语音识别控制相关
    transcription = dict()
    # 角色分离 ： 可选
    transcription['DiarizationEnabled'] = True
    diarization = dict()
    diarization['SpeakerCount'] = 2
    transcription['Diarization'] = diarization
    parameters['Transcription'] = transcription

    # 文本翻译控制相关 ： 可选
    parameters['TranslationEnabled'] = True
    translation = dict()
    translation['TargetLanguages'] = ['en'] # 假设翻译成英文
    parameters['Translation'] = translation

    # 章节速览相关 ： 可选，包括： 标题、议程摘要
    parameters['AutoChaptersEnabled'] = True

    # 智能纪要相关 ： 可选，包括： 待办、关键信息(关键词、重点内容、场景识别)
    parameters['MeetingAssistanceEnabled'] = True
    meetingAssistance = dict()
    meetingAssistance['Types'] = ['Actions', 'KeyInformation']
    parameters['MeetingAssistance'] = meetingAssistance

    # 摘要控制相关 ： 可选，包括： 全文摘要、发言人总结摘要、问答摘要(问答回顾)
    parameters['SummarizationEnabled'] = True
    summarization = dict()
    summarization['Types'] = ['Paragraph', 'Conversational', 'QuestionsAnswering', 'MindMap']
    parameters['Summarization'] = summarization

    # ppt抽取和ppt总结 ： 可选
    parameters['PptExtractionEnabled'] = True
    
    # 口语书面化 ： 可选
    parameters['TextPolishEnabled'] = True

    body['Parameters'] = parameters
    return body

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'realtime')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))


# 示例输出
# {
#     "Code":"0",
#     "Data":{
#         "TaskId":"3190978427bb43z09c01dfff********",
#         "TaskKey":"task16988********",
#         "MeetingJoinUrl":"wss://tingwu-realtime-cn-beijing.aliyuncs.com/api/ws/v1?mc=g9ySw5kiwXM4K7tBnIajKq6Fh9G1aUokzkptBIFixj7e7zv6c8AKxUDTW2Oz8AFFONWXtTQedh-NpKZUffqIYdW7yAlivqlo9B0TdeM88fzgWaYk2Ifg********"
#     },
#     "Message":"success",
#     "RequestId":"6582c654-cc37-4f2d-b80d-e5e7********"
# }


# 实时记录语音推流
# 在完成记录创建后，便可通过听悟提供的交互流程与实现进行会中实时语音推流并接收实时识别结果和翻译结果。

# 结束实时记录
# 当该记录结束时，您务必参考如下内容及时调用API结束该记录。若您之前在创建实时记录时设置了后续的比如摘要、章节速览、智能纪要等功能参数，那么在结束记录之后，该实时记录状态并不是COMPLETED，而是ONGOING，表示此时进入到后处理阶段。

#!/usr/bin/env python
#coding=utf-8

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    body = dict()
    body['AppKey'] = '输入您在听悟管控台创建的Appkey'

    # 基本请求参数
    input = dict()

    #输入语音流格式和采样率和以下参数设置保持一致
    input['TaskId'] = '请输入实时会议的TaskId'
    body['Input'] = input

    return body

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'realtime')
request.add_query_param('operation', 'stop')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))