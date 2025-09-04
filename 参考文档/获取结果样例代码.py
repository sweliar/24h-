# 本文介绍如何查询实时记录的任务状态和结果。

# 任务处理结果查询（可选）

# 基于上一步提交任务后返回的TaskId来查询处理结果。

# 如通过此方式轮询查询结果，注意轮询频率不要过高，以免被限流。比如您可以按每1分钟或每5分钟的频率持续查询。

# 任务完成后的回调通知（可选）

# 使用回调通知的方式来获取结果，不同于主动轮询，您可以在提交任务后，等待服务端处理完成时主动地通知您任务状态。

# 当前我们支持通过HTTP的回调方式将任务处理状态通知到您。

# 查询任务状态和结果
# 查询任务时，您需要将“提交任务”时返回的TaskId作为输入，发起查询请求，根据返回的状态判断任务是否已完成。

# 请求参数




# 参数名

# 类型

# 是否必填

# 说明

# TaskId

# string

# 是

# 您提交任务时返回的TaskId信息

#!/usr/bin/env python
#coding=utf-8

import os
import json
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

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

uri = '/openapi/tingwu/v2/tasks' + '/' + '请输入您提交任务时返回的TaskId'
request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'GET', uri)

response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))


# 示例输出
# 当任务仍在运行中时：
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"ONGOING"
    },
    "Message":"success",
    "RequestId":"5fa32fc6-441f-4dd1-bb86-c030********"
}
# 当任务在运行中但有部分结果时：
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"ONGOING",
        "OutputMp3Path":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_20231101141801.mp3?ExLTAI****************AccessKeyId=LTAI****************&amp;Signature=********JBMijH7wLq0xX6aivHc%3D",
        "Result":{
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_Transcription_20231101141926.json?Expires=1698906034&amp;OSSAcceLTAI****************&amp;Signature=********NJlqSEWJxfkMwjwsHCA%3D"
        }
    },
    "Message":"success",
    "RequestId":"1b20e0d9-c55c-4cc3-85af-80b4********"
}

# 当任务已完成时：
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"COMPLETED",
        "OutputMp3Path":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_20231101141801.mp3?ExLTAI4G4uXHLPwQHj6oX8****AccessKeyId=LTAI****************&amp;Signature=********JBMijH7wLq0xX6aivHc%3D",
        "Result":{
            "AutoChapters":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_AutoChapters_20231101141955.json?Expires=1698906034&amp;OSSAcceLTAI****************&amp;Signature=********Ax9FvifYAO8dj4qzWg%3D",
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_Transcription_20231101141926.json?Expires=1698906034&amp;OSSAccessKeyId=LTAI****************&amp;Signature=********NJlqSEWJxfkMwjwsHCA%3D"
        }
    },
    "Message":"success",
    "RequestId":"1b20e0d9-c55c-4cc3-85af-80b4********"
}
#当任务失败时：
{
    "Code":"0",
    "Data":{
        "TaskId":"b76389677b1441fa82165cb1********",
        "TaskStatus":"FAILED",
        "ErrorCode":"TSC.AudioFileLink",
        "ErrorMessage":"Audio file link invalid."
    },
    "Message":"success",
    "RequestId":"d181d898-b627-4040-b7c9-9563********"
}
