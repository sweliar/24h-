# 专门处理音频采集、流推送和实时转写结果管理
import pyaudio
import threading
import time
import nls
import json
import datetime

class AudioHandler:
    def __init__(self, rate=16000, channels=1, chunk=1024):
        # 音频参数
        self.format = pyaudio.paInt16
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        
        # 状态变量
        self.is_recording = False
        self.audio_stream = None
        self.p = None
        self.push_thread = None
        self.transcription_results = []
        self.on_sentence_callback = None
        
    def set_sentence_callback(self, callback):
        """设置句子结束时的回调函数"""
        self.on_sentence_callback = callback
        
    def start_recording(self, meeting_join_url, output_file=None):
        """开始录音并推流"""
        if not meeting_join_url:
            print("请提供有效的会议加入URL")
            return False
        
        self.is_recording = True
        if output_file:
            print(f"开始录音，记录将保存至: {output_file}")
        else:
            print("开始录音...")
        
        # 创建音频流
        self.p = pyaudio.PyAudio()
        self.audio_stream = self.p.open(format=self.format,
                                       channels=self.channels,
                                       rate=self.rate,
                                       input=True,
                                       frames_per_buffer=self.chunk)
        
        # 创建实时推流线程
        self.push_thread = threading.Thread(target=self._push_audio_stream, args=(meeting_join_url,))
        self.push_thread.start()
        
        return True
    
    def _push_audio_stream(self, meeting_join_url):
        """推送音频流到服务器"""
        try:
            # 初始化实时推流对象
            rm = nls.NlsRealtimeMeeting(
                url=meeting_join_url,
                on_sentence_begin=self._on_sentence_begin,
                on_sentence_end=self._on_sentence_end,
                on_start=self._on_start,
                on_result_changed=self._on_result_changed,
                on_completed=self._on_completed,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 开始推流
            rm.start()
            
            # 持续发送音频数据
            while self.is_recording:
                data = self.audio_stream.read(self.chunk)
                rm.send_audio(data)
                time.sleep(0.01)  # 控制发送速率
            
            # 停止推流
            rm.stop()
        except Exception as e:
            print(f"推流过程中发生错误: {str(e)}")
    
    def stop_recording(self):
        """停止录音"""
        print("正在停止录音...")
        self.is_recording = False
        
        if self.push_thread and self.push_thread.is_alive():
            self.push_thread.join(timeout=5)
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        
        if self.p:
            self.p.terminate()
    
    # 回调函数
    def _on_sentence_begin(self, message, *args):
        """句子开始事件回调"""
        pass
    
    def _on_sentence_end(self, message, *args):
        """句子结束事件回调"""
        try:
            msg = json.loads(message)
            result = msg.get('payload', {}).get('result', '')
            if result:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.transcription_results.append({"timestamp": timestamp, "text": result})
                print(f"[{timestamp}] {result}")
                # 调用回调函数
                if self.on_sentence_callback:
                    self.on_sentence_callback(self.transcription_results)
        except Exception as e:
            print(f"处理句子结束事件时发生错误: {str(e)}")
    
    def _on_start(self, message, *args):
        """开始事件回调"""
        print("实时推流已开始")
    
    def _on_result_changed(self, message, *args):
        """识别结果变化事件回调"""
        pass
    
    def _on_completed(self, message, *args):
        """完成事件回调"""
        print("实时推流已完成")
    
    def _on_error(self, message, *args):
        """错误事件回调"""
        print(f"发生错误: {message}, {args}")
    
    def _on_close(self, *args):
        """关闭事件回调"""
        print(f"连接已关闭: {args}")
    
    def get_transcription_results(self):
        """获取转写结果"""
        return self.transcription_results