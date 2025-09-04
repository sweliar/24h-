#coding=utf-8

import datetime
import time
import sys
import nls

# 导入解耦后的模块
from api_handler import APIHandler
from audio_handler import AudioHandler
from file_handler import FileHandler

class MeetingAssistant:
    def __init__(self):
        # 初始化时间戳
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_file = f"会议记录_{self.timestamp}.txt"
        
        # 初始化各模块
        self.api_handler = APIHandler()
        self.audio_handler = AudioHandler()
        self.file_handler = FileHandler(self.timestamp)
        
        # 设置音频处理器的回调函数
        self.audio_handler.set_sentence_callback(self._on_sentence_complete)
        
        # 任务参数
        self.task_id = ''
        self.meeting_join_url = ''
        
        # 控制标志
        self.is_recording = False
        self.recording_thread = None
    
    def _on_sentence_complete(self, transcription_results):
        """句子完成时的回调，用于实时保存转写结果"""
        self.file_handler.save_transcription_to_file(transcription_results, self.output_file)
    
    def create_realtime_task(self):
        """创建实时记录任务"""
        task_key = 'task' + self.timestamp
        self.task_id, self.meeting_join_url = self.api_handler.create_realtime_task(task_key)
        return self.task_id is not None and self.meeting_join_url is not None
    
    def start_recording(self):
        """开始录音并推流，支持手动按Enter键停止或系统在时间段结束时自动停止"""
        if not self.task_id or not self.meeting_join_url:
            print("请先创建实时记录任务")
            return False
        
        # 开始录音
        success = self.audio_handler.start_recording(self.meeting_join_url, self.output_file)
        if success:
            self.is_recording = True
            print("录音中...")
            print("输入'q'并按Enter键手动停止录音，或系统将在时间段结束时自动停止录音")
            
            # 使用线程持续监听用户输入，允许随时停止
            import threading
            def wait_for_input():
                while self.is_recording:
                    try:
                        # 使用非阻塞方式读取输入
                        import msvcrt
                        if msvcrt.kbhit():
                            key = msvcrt.getch().decode('utf-8')
                            if key == 'q' or key == 'Q':
                                print("\n用户手动停止录音...")
                                self.is_recording = False
                                self.stop_recording()
                                break
                            elif key == '\r':  # Enter键
                                print("\n继续录音中... 输入'q'并按Enter键手动停止录音")
                    except Exception as e:
                        # 如果无法使用msvcrt（例如在某些环境下），回退到input方式
                        try:
                            user_input = input()
                            if user_input.lower() == 'q' and self.is_recording:
                                print("用户手动停止录音...")
                                self.is_recording = False
                                self.stop_recording()
                                break
                        except:
                            pass
                    time.sleep(0.1)  # 短暂休眠避免CPU占用过高
            
            self.recording_thread = threading.Thread(target=wait_for_input)
            self.recording_thread.daemon = False  # 设置为非守护线程，确保用户输入能被正确处理
            self.recording_thread.start()
        
        return success
    
    def stop_recording(self):
        """停止录音"""
        # 设置标志为停止状态
        self.is_recording = False
        
        # 停止音频录制
        self.audio_handler.stop_recording()
        
        # 结束实时记录任务
        self.api_handler.stop_realtime_task(self.task_id)
    
    def process_task_results(self):
        """处理任务结果，获取摘要等"""
        # 等待AI处理结果
        print("\n等待AI处理结果...")
        time.sleep(10)  # 给AI一些处理时间
        
        # 获取任务结果
        result_data = self.api_handler.get_task_result(self.task_id)
        
        # 处理结果数据
        downloaded_files = []
        if result_data and result_data.get('TaskStatus') == 'COMPLETED':
            downloaded_files = self.file_handler.process_task_results(result_data)
            print("已获取完整的会议摘要和分析结果")
        
        return downloaded_files
    
    def run(self, test_mode=False):
        """运行会议助手 - 定时运行模式"""
        print("===== 办公室会议助手 - 定时运行中 ======")
        
        try:
            if test_mode:
                # 测试模式：跳过真实API调用，模拟录音过程
                print("测试模式已启用")
                self.task_id = "test_task_id"
                self.meeting_join_url = "http://test_url"
                
                # 开始模拟录音
                self.is_recording = True
                print("模拟录音中...")
                print("输入'q'并按Enter键手动停止录音")
                
                # 使用线程持续监听用户输入
                import threading
                def wait_for_input():
                    while self.is_recording:
                        try:
                            # 使用非阻塞方式读取输入
                            import msvcrt
                            if msvcrt.kbhit():
                                key = msvcrt.getch().decode('utf-8')
                                if key == 'q' or key == 'Q':
                                    print("\n用户手动停止录音...")
                                    self.is_recording = False
                                    print("录音已停止")
                                    print("模拟完成任务处理")
                                    sys.exit(0)  # 测试模式下完成后退出程序
                                    break
                                elif key == '\r':  # Enter键
                                    print("\n继续录音中... 输入'q'并按Enter键手动停止录音")
                        except Exception as e:
                            # 如果无法使用msvcrt（例如在某些环境下），回退到input方式
                            try:
                                user_input = input()
                                if user_input.lower() == 'q' and self.is_recording:
                                    print("用户手动停止录音...")
                                    self.is_recording = False
                                    print("录音已停止")
                                    print("模拟完成任务处理")
                                    sys.exit(0)  # 测试模式下完成后退出程序
                                    break
                            except:
                                pass
                        time.sleep(0.1)  # 短暂休眠避免CPU占用过高
                
                self.recording_thread = threading.Thread(target=wait_for_input)
                self.recording_thread.daemon = False
                self.recording_thread.start()
                
                return True
            else:
                # 正常模式
                # 创建实时记录任务
                if not self.create_realtime_task():
                    print("创建任务失败，退出本轮运行")
                    return False
                
                # 开始录音
                if not self.start_recording():
                    print("录音失败，退出本轮运行")
                    return False
                
                return True
        except Exception as e:
            print(f"运行过程中发生错误: {str(e)}")
            return False
    
    def wait_and_process_results(self, duration_seconds=None):
        """等待录音结束并处理结果"""
        try:
            # 记录进入方法时的录音状态，用于判断是否是用户手动停止
            initial_is_recording = self.is_recording
            
            # 如果指定了等待时间，则等待指定时间后停止
            if duration_seconds:
                print(f"将在{duration_seconds//3600}小时{(duration_seconds%3600)//60}分钟后自动停止...")
                # 使用循环检查is_recording标志，以便能够响应手动停止
                for _ in range(int(duration_seconds)):
                    if not self.is_recording:
                        break
                    time.sleep(1)
            
            # 如果录音仍在进行中，才调用停止录音（避免重复停止）
            if self.is_recording:
                self.stop_recording()
            
            # 保存最终转写结果
            self.file_handler.save_transcription_to_file(
                self.audio_handler.get_transcription_results(), 
                self.output_file
            )
            
            # 处理任务结果（获取摘要等）
            downloaded_files = self.process_task_results()
            
            print("\n===== 本轮会议助手已完成工作 ======")
            print("\n生成的文件:")
            print(f"- 实时会议记录: {self.output_file}")
            
            # 打印所有下载的文件
            for file in downloaded_files:
                if file != self.output_file:
                    print(f"- {file}")
                      
            # 返回是否是用户手动停止的标记
            # 如果进入方法时录音在进行中，但现在停止了，则表示是用户手动停止的
            is_manually_stopped = initial_is_recording and not self.is_recording
            return downloaded_files, is_manually_stopped
        except Exception as e:
            print(f"处理结果时发生错误: {str(e)}")
            return [], False

def wait_until_next_run_time():
    """等待到下一个运行时间段开始"""
    while True:
        now = datetime.datetime.now()
        current_time = now.time()
        
        # 检查是否在上午时间段内 (10:00-12:30)
        morning_start = datetime.time(10, 0)
        morning_end = datetime.time(12, 30)
        if morning_start <= current_time < morning_end:
            print(f"当前时间在上午运行时间段内: {current_time}")
            return True
        
        # 检查是否在下午时间段内 (13:30-21:00)
        afternoon_start = datetime.time(13, 30)
        afternoon_end = datetime.time(21, 0)
        if afternoon_start <= current_time < afternoon_end:
            print(f"当前时间在下午运行时间段内: {current_time}")
            return True
        
        # 计算距离下一个运行时间段的等待时间
        if current_time < morning_start:
            # 等待到上午开始时间
            next_run = datetime.datetime.combine(now.date(), morning_start)
            wait_seconds = (next_run - now).total_seconds()
            print(f"当前时间不在运行时间段内，将在 {morning_start} 开始运行，还需等待: {wait_seconds//3600}小时{(wait_seconds%3600)//60}分钟")
        elif current_time < afternoon_start:
            # 等待到下午开始时间
            next_run = datetime.datetime.combine(now.date(), afternoon_start)
            wait_seconds = (next_run - now).total_seconds()
            print(f"当前时间不在运行时间段内，将在 {afternoon_start} 开始运行，还需等待: {wait_seconds//3600}小时{(wait_seconds%3600)//60}分钟")
        else:
            # 等待到第二天上午开始时间
            next_day = now.date() + datetime.timedelta(days=1)
            next_run = datetime.datetime.combine(next_day, morning_start)
            wait_seconds = (next_run - now).total_seconds()
            print(f"当前时间不在运行时间段内，将在明天 {morning_start} 开始运行，还需等待: {wait_seconds//3600}小时{(wait_seconds%3600)//60}分钟")
        
        # 等待60秒后再次检查时间，避免系统时间变化导致的问题
        time.sleep(60)

if __name__ == "__main__":
    # 启用nls日志（可选）
    nls.enableTrace(False)
    
    # 检查是否启用测试模式
    test_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode = True
        print("===== 办公室会议助手 - 测试模式 =====")
    else:
        print("===== 办公室会议助手 - 定时运行模式 =====")
        print("运行时间段设置：")
        print("- 上午：10:00 - 12:30")
        print("- 下午：13:30 - 21:00")
        print("注：API支持24小时单次记录，程序将在每个时间段内持续录音直到时间段结束")
        print("提示：可以使用 python main.py --test 命令进入测试模式，直接测试录音停止功能")
    
    if test_mode:
        # 测试模式：直接运行助手，测试输入'q'停止录音功能
        assistant = MeetingAssistant()
        assistant.run(test_mode=True)
    else:
        # 正常模式：按时间计划运行
        while True:
            try:
                # 检查是否在运行时间段内
                if wait_until_next_run_time():
                    now = datetime.datetime.now()
                    current_time = now.time()
                    
                    # 确定当前时间段的结束时间
                    if datetime.time(10, 0) <= current_time < datetime.time(12, 30):
                        # 上午时间段
                        end_time = datetime.datetime.combine(now.date(), datetime.time(12, 30))
                        print(f"当前为上午时间段，将持续到上午12:30")
                    elif datetime.time(13, 30) <= current_time < datetime.time(21, 0):
                        # 下午时间段
                        end_time = datetime.datetime.combine(now.date(), datetime.time(21, 0))
                        print(f"当前为下午时间段，将持续到晚上21:00")
                    
                    # 在当前时间段内循环运行录音任务
                    while True:
                        # 检查是否仍在运行时间段内
                        current_time = datetime.datetime.now().time()
                        if (end_time.time() == datetime.time(12, 30) and (current_time >= datetime.time(12, 30) or current_time < datetime.time(10, 0))) or \
                           (end_time.time() == datetime.time(21, 0) and (current_time >= datetime.time(21, 0) or current_time < datetime.time(13, 30))):
                            print("当前时间段已结束")
                            break
                        
                        # 创建并运行会议助手
                        print("\n正在准备新的会议记录任务...")
                        assistant = MeetingAssistant()
                        if assistant.run():
                            # 计算剩余时间
                            now_in_segment = datetime.datetime.now()
                            remaining_seconds = (end_time - now_in_segment).total_seconds()
                            if remaining_seconds <= 0:
                                break
                            
                            # 等待指定时间后处理结果
                            downloaded_files, is_manually_stopped = assistant.wait_and_process_results(remaining_seconds)
                            
                            if is_manually_stopped:
                                # 如果是用户手动停止的，立即准备开始新的录音任务
                                print("用户手动停止当前录音任务，准备开始新的录音任务")
                                # 短暂等待，避免创建任务过于频繁
                                time.sleep(5)
                            else:
                                # 如果是自动停止的（时间段结束），退出当前时间段的循环
                                print("当前时间段的会议记录已完成")
                                break
                        else:
                            print("会议记录启动失败，5秒后重试")
                            time.sleep(5)
                    
                print("程序将继续运行并在适当时间自动开始新的录音")
            except Exception as e:
                print(f"程序运行出错: {str(e)}")
                print("错误已处理，程序将继续运行并在适当时间自动开始新的录音")
                # 短暂等待后继续，避免错误过于频繁
                time.sleep(60)