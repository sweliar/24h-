# 邮箱配置 (Exchange协议)
#coding=utf-8

# SMTP邮件配置
SMTP_SERVER = "mail.lexin.com" #SMTP服务器地址
SMTP_PORT = 25
SENDER_EMAIL = "YOUR_EMAIL" #发送邮箱 
SENDER_PASSWORD = "YOUR_PASSWORD"
RECEIVER_EMAIL = "RECEIVER_EMAIL"# 接收人邮箱

# 阿里云API配置信息
# 通义听悟API配置
# APP_KEY = "shu"
# ACCESS_KEY_ID = "TM"
# ACCESS_KEY_SECRET = "1"

# 区域ID
REGION_ID = 'cn-beijing'

# 音频参数配置
AUDIO_FORMAT = 1  # 1表示pcm格式
AUDIO_CHANNELS = 1  # 单声道
AUDIO_RATE = 16000  # 采样率
AUDIO_CHUNK = 1024  # 音频块大小

# 任务参数配置
MAX_RETRIES = 30  # 查询任务结果的最大重试次数
RETRY_INTERVAL = 60  # 查询任务结果的重试间隔(秒)
WAIT_AI_PROCESSING_TIME = 10  # 等待AI处理的时间(秒)

# 功能开关配置
ENABLE_DIARIZATION = True  # 启用角色分离
SPEAKER_COUNT = 0  # 发言人数量
ENABLE_SUMMARIZATION = True  # 启用摘要生成
ENABLE_AUTO_CHAPTERS = True  # 启用章节速览
ENABLE_MEETING_ASSISTANCE = True  # 启用智能纪要

# 摘要类型配置
SUMMARY_TYPES = ['Paragraph', 'Conversational', 'QuestionsAnswering']

# 智能纪要类型配置
#Actions：待办事项
#KeyInformation：关键信息处理，含关键词、重点内容等
ASSISTANCE_TYPES = ['KeyInformation']

# 日志配置
ENABLE_TRACE_LOG = False  # 启用详细日志输出