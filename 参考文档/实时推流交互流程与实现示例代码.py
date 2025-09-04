# 前提条件
# 安装智能语音交互实时转写SDK

# 创建实时记录并成功获得推流地址

# 示例代码
import time
import threading
import sys
import nls

class TestRealtimeMeeting:
    def __init__(self, tid, test_file, url):
        self.__th = threading.Thread(target=self.__test_run)
        self.__id = tid
        self.__test_file = test_file
        self.__url = url

    def loadfile(self, filename):
        with open(filename, "rb") as f:
            self.__data = f.read()

    def start(self):
        self.loadfile(self.__test_file)
        self.__th.start()

    def test_on_sentence_begin(self, message, *args):
        print("test_on_sentence_begin:{}".format(message))

    def test_on_sentence_end(self, message, *args):
        print("test_on_sentence_end:{}".format(message))

    def test_on_start(self, message, *args):
        print("test_on_start:{}".format(message))

    def test_on_error(self, message, *args):
        print("on_error message=>{} args=>{}".format(message, args))

    def test_on_close(self, *args):
        print("on_close: args=>{}".format(args))

    def test_on_result_chg(self, message, *args):
        print("test_on_chg:{}".format(message))

    def test_on_result_translated(self, message, *args):
        print("test_on_translated:{}".format(message))

    def test_on_completed(self, message, *args):
        print("on_completed:args=>{} message=>{}".format(args, message))

    def __test_run(self):
        print("thread:{} start..".format(self.__id))
        rm = nls.NlsRealtimeMeeting(
                    url=self.__url,
                    on_sentence_begin=self.test_on_sentence_begin,
                    on_sentence_end=self.test_on_sentence_end,
                    on_start=self.test_on_start,
                    on_result_changed=self.test_on_result_chg,
                    on_result_translated=self.test_on_result_translated,
                    on_completed=self.test_on_completed,
                    on_error=self.test_on_error,
                    on_close=self.test_on_close,
                    callback_args=[self.__id]
                )

        print("{}: session start".format(self.__id))
        r = rm.start()

        self.__slices = zip(*(iter(self.__data),) * 640)
        for i in self.__slices:
            rm.send_audio(bytes(i))
            time.sleep(0.01)

        time.sleep(1)

        r = rm.stop()
        print("{}: rm stopped:{}".format(self.__id, r))
        time.sleep(5)

def multiruntest(num=1):
    for i in range(0, num):
        name = "thread" + str(i)
        t = TestRealtimeMeeting(name, "nls-sample-16k.wav",
                                "请输入您创建实时会议时返回的MeetingJoinUrl")
        t.start()

nls.enableTrace(False)
multiruntest(1)




# 句子开始事件表示服务端检测到了一句话的开始，听悟服务的智能断句功能会判断出一句话的开始与结束，示例如下。

 
{
    "header":{
        "namespace":"SpeechTranscriber",
        "name":"SentenceBegin",
        "status":20000000,
        "message_id":"a426f3d4618447519c9d85d1a0d1****",
        "task_id":"5ec521b5aa104e3abccf3d361822****",
        "status_text":"Gateway:SUCCESS:Success."
    },
    "payload":{
        "index":0,
        "time":0
    }
}


# 句中识别结果变化事件（TranscriptionResultChanged）

# 句中识别结果变化事件表示识别结果发生了变化，示例如下。

 
{
    "header":{
        "namespace":"SpeechTranscriber",
        "name":"TranscriptionResultChanged",
        "status":20000000,
        "message_id":"dc21193fada84380a3b6137875ab****",
        "task_id":"5ec521b5aa104e3abccf3d361822****",
        "status_text":"Gateway:SUCCESS:Success."
    },
    "payload":{
        "index":0,
        "time":1835,
        "result":"北京的天",
        "words":[
            {
                "text":"北京",
                "startTime":630,
                "endTime":930
            },
            {
                "text":"的",
                "startTime":930,
                "endTime":1110
            },
            {
                "text":"天",
                "startTime":1110,
                "endTime":1140
            }
        ]
    }
}

# 句子结束事件（SentenceEnd）

# 句子结束事件表示服务端检测到了一句话的结束，并附带返回该句话的识别结果，示例如下。

 
{
    "header":{
        "namespace":"SpeechTranscriber",
        "name":"SentenceEnd",
        "status":20000000,
        "message_id":"c3a9ae4b231649d5ae05d4af36fd****",
        "task_id":"5ec521b5aa104e3abccf3d361822****",
        "status_text":"Gateway:SUCCESS:Success."
    },
    "payload":{
        "index":0,
        "time":1835,
        "result":"北京的天气",
        "words":[
            {
                "text":"北京",
                "startTime":630,
                "endTime":930
            },
            {
                "text":"的",
                "startTime":930,
                "endTime":1110
            },
            {
                "text":"天气",
                "startTime":1110,
                "endTime":1140
            }
        ],
        "stash_result": {
            "index": 1,
            "currentTime": 1140,
            "words": [
                {
                    "startTime": 1150,
                    "text": "会",
                    "endTime": 1190
                },
                {
                    "startTime": 1190,
                    "text": "下雨",
                    "endTime": 1320
                }
            ],
            "beginTime": 1140,
            "text": "会下雨"
        }
    }
}

# 识别结果翻译事件（ResultTranslated）

# 识别结果翻译事件表示在开启翻译时服务端检测到识别结果并进行目标语言文本翻译，示例如下

{
    "header":{
        "namespace":"SpeechTranscriber",
        "name":"ResultTranslated",
        "status":20000000,
        "message_id":"c3a9ae4b231649d5ae05d4af36fd****",
        "task_id":"5ec521b5aa104e3abccf3d361822****",
        "status_text":"Gateway:SUCCESS:Success.",
        "source_message_id":"d4a9ae4b231649d5ae05d4af36fd****"
    },
    "payload":{
        "speaker_id":"xxx",
        "source_lang":"cn",
        "target_lang":"en",
        "translate_result":[
            {
                "text":"At that time.",
                "index":110,
                "beginTime":123000,
                "endTime":125000
            },
            {
                "text":"xxx",
                "index":111,
                "partial":true
            }
        ]
    }
}
