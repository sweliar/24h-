#负责文件下载、转写结果和摘要的保存与格式化
import json
import datetime
import requests
import os

class FileHandler:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        # 从时间戳提取年月日，格式为：YYYY-MM-DD
        date_part = timestamp[:8]  # 假设timestamp格式为：YYYYMMDD_HHMMSS
        year = date_part[:4]
        month = date_part[4:6]
        day = date_part[6:8]
        self.date_folder = f"{year}-{month}-{day}"
        
        # 创建会议结果目录下的日期文件夹
        self.output_directory = os.path.join("会议结果", self.date_folder)
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
            print(f"创建目录: {self.output_directory}")
        
    def download_oss_file(self, url, output_path):
        """从OSS链接下载文件"""
        try:
            # 构建完整的文件路径
            full_output_path = os.path.join(self.output_directory, output_path)
            print(f"正在下载文件: {full_output_path}")
            response = requests.get(url.strip(), timeout=30)
            response.raise_for_status()
            
            # 如果是JSON文件，解析并格式化
            if output_path.endswith('.json'):
                try:
                    data = response.json()
                    with open(full_output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    # 如果不是有效JSON，直接保存内容
                    with open(full_output_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
            else:
                with open(full_output_path, 'wb') as f:
                    f.write(response.content)
            
            print(f"文件下载完成: {full_output_path}")
            return full_output_path
        except Exception as e:
            print(f"下载文件时发生错误: {str(e)}")
            return None
    
    def save_transcription_to_file(self, transcription_results, output_file):
        """将转写结果保存到本地文件"""
        if not transcription_results:
            print("没有转写结果可保存")
            return False
        
        try:
            # 构建完整的文件路径
            full_output_path = os.path.join(self.output_directory, output_file)
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(f"会议记录 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                for item in transcription_results:
                    f.write(f"[{item['timestamp']}] {item['text']}\n")
            
            print(f"转写结果已保存至: {full_output_path}")
            return full_output_path
        except Exception as e:
            print(f"保存转写结果时发生错误: {str(e)}")
            return False
    
    def save_complete_transcription(self, transcription_data):
        """保存完整的转写结果到本地文件"""
        try:
            output_file = f"完整会议记录_{self.timestamp}.txt"
            # 构建完整的文件路径
            full_output_path = os.path.join(self.output_directory, output_file)
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(f"完整会议记录 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                # 检查数据结构并提取转写文本
                if isinstance(transcription_data, dict):
                    if 'Sentences' in transcription_data:
                        for sentence in transcription_data['Sentences']:
                            if 'Text' in sentence:
                                speaker = sentence.get('SpeakerId', '未知')
                                timestamp = datetime.datetime.fromtimestamp(sentence.get('StartTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
                                f.write(f"[{timestamp}] [发言人{speaker}] {sentence['Text']}\n")
                    elif 'Text' in transcription_data:
                        f.write(transcription_data['Text'])
                    else:
                        # 如果找不到明确的转写文本字段，保存整个JSON
                        f.write(json.dumps(transcription_data, ensure_ascii=False, indent=2))
                else:
                    f.write(str(transcription_data))
            
            print(f"完整转写结果已保存至: {full_output_path}")
            return full_output_path
        except Exception as e:
            print(f"保存完整转写结果时发生错误: {str(e)}")
            return None
    
    def save_summarization(self, summarization_data):
        """保存会议摘要到本地文件"""
        try:
            output_file = f"会议摘要_{self.timestamp}.txt"
            # 构建完整的文件路径
            full_output_path = os.path.join(self.output_directory, output_file)
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(f"会议摘要 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                # 检查数据结构并提取摘要内容
                if isinstance(summarization_data, dict):
                    # 段落式摘要
                    if 'Paragraph' in summarization_data:
                        f.write("【段落式摘要】\n")
                        f.write(summarization_data['Paragraph'] + "\n\n")
                    
                    # 对话式摘要
                    if 'Conversational' in summarization_data:
                        f.write("【对话式摘要】\n")
                        for item in summarization_data['Conversational']:
                            f.write(f"{item}\n")
                        f.write("\n")
                    
                    # 问答式摘要
                    if 'QuestionsAnswering' in summarization_data:
                        f.write("【问答式摘要】\n")
                        for qa in summarization_data['QuestionsAnswering']:
                            f.write(f"问: {qa.get('Question', '')}\n")
                            f.write(f"答: {qa.get('Answer', '')}\n\n")
                    
                    # 思维导图式摘要（如果有）
                    if 'MindMap' in summarization_data:
                        f.write("【思维导图式摘要】\n")
                        # 简单格式展示思维导图结构
                        for key, value in summarization_data['MindMap'].items():
                            f.write(f"{key}:\n")
                            if isinstance(value, list):
                                for item in value:
                                    f.write(f"  - {item}\n")
                            else:
                                f.write(f"  {value}\n")
                        f.write("\n")
                else:
                    f.write(str(summarization_data))
            
            print(f"会议摘要已保存至: {full_output_path}")
            return full_output_path
        except Exception as e:
            print(f"保存会议摘要时发生错误: {str(e)}")
            return None
    
    def process_task_results(self, task_result):
        """处理任务结果，下载并保存所有相关文件"""
        try:
            downloaded_files = []
            
            # 获取结果中的OSS链接
            if 'Result' in task_result:
                result = task_result['Result']
                
                # 下载并处理转写结果
                if 'Transcription' in result:
                    transcription_url = result['Transcription']
                    transcription_file = f"转写原始数据_{self.timestamp}.json"
                    if self.download_oss_file(transcription_url, transcription_file):
                        downloaded_files.append(transcription_file)
                        # 读取并处理转写文件
                        try:
                            with open(os.path.join(self.output_directory, transcription_file), 'r', encoding='utf-8') as f:
                                transcription_data = json.load(f)
                            complete_trans_file = self.save_complete_transcription(transcription_data)
                            if complete_trans_file:
                                downloaded_files.append(complete_trans_file)
                        except Exception as e:
                            print(f"处理转写文件时发生错误: {str(e)}")
                
                # 下载并处理摘要结果
                if 'Summarization' in result:
                    summarization_url = result['Summarization']
                    summarization_file = f"摘要原始数据_{self.timestamp}.json"
                    if self.download_oss_file(summarization_url, summarization_file):
                        downloaded_files.append(summarization_file)
                        # 读取并处理摘要文件
                        try:
                            with open(os.path.join(self.output_directory, summarization_file), 'r', encoding='utf-8') as f:
                                summarization_data = json.load(f)
                            summary_file = self.save_summarization(summarization_data)
                            if summary_file:
                                downloaded_files.append(summary_file)
                        except Exception as e:
                            print(f"处理摘要文件时发生错误: {str(e)}")
                
                # 下载并保存章节速览
                if 'AutoChapters' in result:
                    chapters_url = result['AutoChapters']
                    chapters_file = f"章节速览_{self.timestamp}.json"
                    if self.download_oss_file(chapters_url, chapters_file):
                        downloaded_files.append(chapters_file)
                
                # 下载并保存智能纪要
                if 'MeetingAssistance' in result:
                    assistance_url = result['MeetingAssistance']
                    assistance_file = f"智能纪要_{self.timestamp}.json"
                    if self.download_oss_file(assistance_url, assistance_file):
                        downloaded_files.append(assistance_file)
            
            # 下载音频文件
            if 'OutputMp3Path' in task_result:
                audio_url = task_result['OutputMp3Path']
                audio_file = f"会议音频_{self.timestamp}.mp3"
                if self.download_oss_file(audio_url, audio_file):
                    downloaded_files.append(audio_file)
            
            return downloaded_files
        except Exception as e:
            print(f"处理任务结果时发生错误: {str(e)}")
            return []