# 负责与阿里云通义听悟API的所有交互，包括任务创建、查询和结束

import json
import time
import sys
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential
import config_local

class APIHandler:
    def __init__(self, app_key=None, access_key_id=None, access_key_secret=None, region_id='cn-beijing'):
        self.app_key = app_key or config_local.APP_KEY
        self.access_key_id = access_key_id or config_local.ACCESS_KEY_ID
        self.access_key_secret = access_key_secret or config_local.ACCESS_KEY_SECRET
        self.region_id = region_id
        self.client = self._init_client()
        
    def _init_client(self):
        """初始化AcsClient"""
        if not self.access_key_id or not self.access_key_secret:
            print("请在config_local.py中设置ACCESS_KEY_ID和ACCESS_KEY_SECRET")
            sys.exit(1)
        
        credentials = AccessKeyCredential(self.access_key_id, self.access_key_secret)
        return AcsClient(region_id=self.region_id, credential=credentials)
    
    def create_common_request(self, domain, version, protocol_type, method, uri):
        """创建通用请求"""
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain(domain)
        request.set_version(version)
        request.set_protocol_type(protocol_type)
        request.set_method(method)
        request.set_uri_pattern(uri)
        request.add_header('Content-Type', 'application/json')
        return request
    
    def create_realtime_task(self, task_key, rate=16000, speaker_count=2):
        """创建实时记录任务"""
        print("正在创建实时记录任务...")
        
        # 初始化参数
        body = dict()
        body['AppKey'] = self.app_key
        
        # 基本请求参数
        input_params = dict()
        input_params['Format'] = 'pcm'
        input_params['SampleRate'] = rate
        input_params['SourceLanguage'] = 'cn'
        input_params['TaskKey'] = task_key
        input_params['ProgressiveCallbacksEnabled'] = False
        body['Input'] = input_params
        
        # AI相关参数
        parameters = dict()
        
        # 语音识别控制
        transcription = dict()
        transcription['DiarizationEnabled'] = True
        diarization = dict()
        diarization['SpeakerCount'] = speaker_count
        transcription['Diarization'] = diarization
        parameters['Transcription'] = transcription
        
        # 摘要控制
        parameters['SummarizationEnabled'] = True
        summarization = dict()
        summarization['Types'] = ['Paragraph', 'Conversational', 'QuestionsAnswering']
        parameters['Summarization'] = summarization
        
        # 章节速览
        parameters['AutoChaptersEnabled'] = True
        
        # 智能纪要
        parameters['MeetingAssistanceEnabled'] = True
        meeting_assistance = dict()
        meeting_assistance['Types'] = ['Actions', 'KeyInformation']
        parameters['MeetingAssistance'] = meeting_assistance
        
        body['Parameters'] = parameters
        
        # 发送请求
        request = self.create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
        request.add_query_param('type', 'realtime')
        request.set_content(json.dumps(body).encode('utf-8'))
        
        try:
            response = self.client.do_action_with_exception(request)
            result = json.loads(response)
            print(f"任务创建成功: {result}")
            
            if result.get('Code') == '0':
                task_id = result['Data']['TaskId']
                meeting_join_url = result['Data']['MeetingJoinUrl']
                print(f"TaskId: {task_id}")
                print(f"MeetingJoinUrl: {meeting_join_url}")
                return task_id, meeting_join_url
            else:
                print(f"任务创建失败: {result.get('Message')}")
                return None, None
        except Exception as e:
            print(f"创建任务时发生错误: {str(e)}")
            return None, None
    
    def stop_realtime_task(self, task_id):
        """结束实时记录任务"""
        if not task_id:
            print("没有活动的任务")
            return
        
        print("正在结束实时记录任务...")
        
        # 初始化参数
        body = dict()
        body['AppKey'] = self.app_key
        
        # 基本请求参数
        input_params = dict()
        input_params['TaskId'] = task_id
        body['Input'] = input_params
        
        # 发送请求
        request = self.create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
        request.add_query_param('type', 'realtime')
        request.add_query_param('operation', 'stop')
        request.set_content(json.dumps(body).encode('utf-8'))
        
        try:
            response = self.client.do_action_with_exception(request)
            result = json.loads(response)
            print(f"任务结束响应: {result}")
        except Exception as e:
            print(f"结束任务时发生错误: {str(e)}")
    
    def get_task_result(self, task_id, max_retries=30, retry_interval=60):
        """查询任务结果"""
        if not task_id:
            print("没有活动的任务")
            return None
        
        print("正在查询任务结果，这可能需要一些时间...")
        
        uri = f'/openapi/tingwu/v2/tasks/{task_id}'
        request = self.create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'GET', uri)
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                response = self.client.do_action_with_exception(request)
                result = json.loads(response)
                print(f"任务结果查询响应: {result}")
                
                if result.get('Code') == '0':
                    task_status = result['Data'].get('TaskStatus')
                    print(f"任务状态: {task_status}")
                    
                    if task_status == 'COMPLETED':
                        print("任务已完成，可获取完整结果")
                        return result['Data']
                    elif task_status == 'ONGOING':
                        print(f"任务正在处理中，{retry_interval}秒后再次查询...")
                        time.sleep(retry_interval)
                        retry_count += 1
                else:
                    print(f"查询任务结果失败: {result.get('Message')}")
                    return None
            except Exception as e:
                print(f"查询任务结果时发生错误: {str(e)}")
                return None
        
        print("查询超时，您可以稍后手动查询任务结果")
        return None