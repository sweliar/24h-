import os
import sys
import time
import datetime
import re
from flask import Flask, render_template, jsonify, request, send_file
import threading
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import MeetingAssistant

app = Flask(__name__)

# 运行模式配置文件路径
MODE_CONFIG_FILE = 'run_mode_config.json'

# 加载或初始化运行模式配置
def load_run_mode_config():
    if os.path.exists(MODE_CONFIG_FILE):
        try:
            with open(MODE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # 默认配置
    return {
        'mode': 'manual',  # manual, full_day, custom
        'full_day': {
            'morning_start': '10:00',
            'morning_end': '12:30',
            'afternoon_start': '13:30',
            'afternoon_end': '21:00'
        },
        'custom': {
            'periods': []  # 自定义时段，格式：[{start: 'HH:MM', end: 'HH:MM'}]
        }
    }

# 保存运行模式配置
def save_run_mode_config(config):
    try:
        with open(MODE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# 全局运行模式配置
run_mode_config = load_run_mode_config()

# 历史录音记录存储
recording_history = []

# 历史记录文件路径
HISTORY_FILE = 'recording_history.json'

# 加载历史录音记录
def load_recording_history():
    global recording_history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                recording_history = json.load(f)
        except:
            recording_history = []
    else:
        recording_history = []

# 保存历史录音记录
def save_recording_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(recording_history, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# 添加录音记录到历史

def add_recording_to_history(task_id, start_time, end_time, output_file):
    global recording_history
    
    # 创建新的历史记录
    new_record = {
        'id': task_id,
        'start_time': start_time,
        'end_time': end_time,
        'output_file': output_file,
        'duration': calculate_duration(start_time, end_time),
        'date': start_time.split(' ')[0]  # 提取日期部分
    }
    
    # 添加到历史记录列表的开头（最新的在前）
    recording_history.insert(0, new_record)
    
    # 限制历史记录数量，避免文件过大
    max_history = 1000  # 最多保留1000条记录
    if len(recording_history) > max_history:
        recording_history = recording_history[:max_history]
    
    # 保存历史记录
    save_recording_history()

# 计算录音持续时间
def calculate_duration(start_time_str, end_time_str):
    try:
        if not start_time_str or not end_time_str:
            return '未知'
        
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        
        duration = end_time - start_time
        seconds = duration.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f'{hours}小时{minutes}分钟{seconds}秒'
        elif minutes > 0:
            return f'{minutes}分钟{seconds}秒'
        else:
            return f'{seconds}秒'
    except:
        return '未知'

# 初始化加载历史记录
load_recording_history()

# 全局变量用于存储当前的会议助手实例
current_assistant = None
recording_status = {
    'is_recording': False,
    'task_id': '',
    'start_time': '',
    'end_time': '',
    'output_file': ''
}

scheduled_tasks = []

# 全局变量用于存储实时转写结果
live_transcription = []

# 结果文件根目录
RESULTS_ROOT_DIR = '会议结果'

# 重写MeetingAssistant的_on_sentence_complete方法，以便实时捕获转写结果
original_on_sentence_complete = MeetingAssistant._on_sentence_complete

def custom_on_sentence_complete(self, transcription_results):
    # 调用原始方法保存到文件
    result = original_on_sentence_complete(self, transcription_results)
    # 同时保存到全局变量供前端使用
    global live_transcription
    for item in transcription_results:
        live_transcription.append({
            'timestamp': item['timestamp'],
            'text': item['text'],
            'time': datetime.datetime.now().strftime('%H:%M:%S')
        })
        # 限制存储的条目数量，避免内存占用过大
        if len(live_transcription) > 500:
            live_transcription = live_transcription[-500:]
    return result

# 替换原始方法
MeetingAssistant._on_sentence_complete = custom_on_sentence_complete

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取当前录音状态"""
    global recording_status
    return jsonify(recording_status)

@app.route('/api/start', methods=['POST'])
def start_recording():
    """开始录音"""
    global current_assistant, recording_status
    
    try:
        # 创建新的会议助手实例
        current_assistant = MeetingAssistant()
        
        # 创建实时任务
        if not current_assistant.create_realtime_task():
            return jsonify({'success': False, 'message': '创建任务失败'})
        
        # 开始录音
        if not current_assistant.start_recording():
            return jsonify({'success': False, 'message': '录音失败'})
        
        # 更新状态
        recording_status = {
            'is_recording': True,
            'task_id': current_assistant.task_id,
            'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': '',
            'output_file': current_assistant.output_file
        }
        
        return jsonify({'success': True, 'message': '录音已开始', 'status': recording_status})
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})

@app.route('/api/stop', methods=['POST'])
def stop_recording():
    """停止录音"""
    global current_assistant, recording_status
    
    try:
        if current_assistant and recording_status['is_recording']:
            current_assistant.stop_recording()
            
            # 更新状态
            recording_status['is_recording'] = False
            recording_status['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 添加到历史记录
            add_recording_to_history(
                recording_status['task_id'],
                recording_status['start_time'],
                recording_status['end_time'],
                recording_status['output_file']
            )
            
            # 处理任务结果，确保文件下载保存
            try:
                # 等待AI处理结果
                print("等待AI处理结果...")
                time.sleep(10)  # 给AI一些处理时间
                
                # 处理任务结果
                downloaded_files = current_assistant.process_task_results()
                print(f"已下载文件: {downloaded_files}")
            except Exception as e:
                print(f"处理任务结果时发生错误: {str(e)}")
            
            return jsonify({'success': True, 'message': '录音已停止', 'status': recording_status})
        else:
            return jsonify({'success': False, 'message': '当前没有正在进行的录音'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})

@app.route('/api/schedule', methods=['POST'])
def schedule_recording():
    """预约录音"""
    global scheduled_tasks
    
    try:
        data = request.json
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        
        if not start_time_str or not end_time_str:
            return jsonify({'success': False, 'message': '请提供开始时间和结束时间'})
        
        # 转换时间字符串为datetime对象
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        
        if start_time <= datetime.datetime.now():
            return jsonify({'success': False, 'message': '开始时间必须大于当前时间'})
        
        if end_time <= start_time:
            return jsonify({'success': False, 'message': '结束时间必须大于开始时间'})
        
        # 计算等待时间
        wait_seconds = (start_time - datetime.datetime.now()).total_seconds()
        
        # 创建任务ID
        task_id = f'schedule_{int(time.time())}'
        
        # 创建并启动预约任务线程
        def scheduled_task():
            # 等待到开始时间
            time.sleep(wait_seconds)
            
            # 开始录音
            global current_assistant, recording_status
            try:
                current_assistant = MeetingAssistant()
                if current_assistant.create_realtime_task() and current_assistant.start_recording():
                    recording_status = {
                        'is_recording': True,
                        'task_id': current_assistant.task_id,
                        'start_time': start_time_str,
                        'end_time': end_time_str,
                        'output_file': current_assistant.output_file
                    }
                    
                    # 计算录音持续时间
                    duration_seconds = (end_time - start_time).total_seconds()
                    
                    # 等待录音结束
                    time.sleep(duration_seconds)
                    
                    # 停止录音
                    if current_assistant and recording_status['is_recording']:
                        current_assistant.stop_recording()
                        recording_status['is_recording'] = False
            except Exception as e:
                print(f'预约任务执行失败: {str(e)}')
        
        # 启动线程
        thread = threading.Thread(target=scheduled_task)
        thread.daemon = True
        thread.start()
        
        # 添加到预约任务列表
        scheduled_tasks.append({
            'id': task_id,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'status': 'scheduled'
        })
        
        return jsonify({
            'success': True,
            'message': f'已预约录音，将在{start_time_str}开始，{end_time_str}结束',
            'task_id': task_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})

@app.route('/api/scheduled_tasks', methods=['GET'])
def get_scheduled_tasks():
    """获取所有预约任务"""
    global scheduled_tasks
    return jsonify(scheduled_tasks)

@app.route('/api/delete_scheduled', methods=['POST'])
def delete_scheduled_task():
    """取消预约任务"""
    global scheduled_tasks
    
    try:
        data = request.json
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'success': False, 'message': '请提供任务ID'})
        
        # 过滤掉指定的任务
        original_length = len(scheduled_tasks)
        scheduled_tasks = [task for task in scheduled_tasks if task['id'] != task_id]
        
        if len(scheduled_tasks) < original_length:
            return jsonify({'success': True, 'message': '预约任务已取消'})
        else:
            return jsonify({'success': False, 'message': '未找到指定的任务'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})

@app.route('/api/transcription', methods=['GET'])
def get_transcription():
    """获取实时转写结果"""
    global live_transcription
    # 获取请求参数，支持从特定索引开始获取新内容
    start_index = request.args.get('start_index', 0, type=int)
    # 返回从start_index开始的新内容
    new_transcriptions = live_transcription[start_index:]
    return jsonify({
        'success': True,
        'transcriptions': new_transcriptions,
        'total_count': len(live_transcription)
    })

@app.route('/api/results', methods=['GET'])
def get_results():
    """获取任务返回结果"""
    global current_assistant
    
    if not current_assistant or not current_assistant.task_id:
        return jsonify({
            'success': False,
            'message': '当前没有任务结果'
        })
    
    try:
        # 尝试获取任务结果
        result_data = current_assistant.api_handler.get_task_result(current_assistant.task_id)
        
        if result_data and result_data.get('TaskStatus') == 'COMPLETED':
            # 处理结果数据并返回
            return jsonify({
                'success': True,
                'results_available': True,
                'task_status': 'COMPLETED',
                'result_data': result_data
            })
        else:
            # 返回任务状态
            return jsonify({
                'success': True,
                'results_available': False,
                'task_status': result_data.get('TaskStatus', 'UNKNOWN') if result_data else 'UNKNOWN'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取结果时发生错误: {str(e)}'
        })

@app.route('/api/clear_transcription', methods=['POST'])
def clear_transcription():
    """清除实时转写结果"""
    global live_transcription
    live_transcription = []
    return jsonify({'success': True, 'message': '转写结果已清除'})

@app.route('/api/run_mode', methods=['GET'])
def get_run_mode():
    """获取当前运行模式配置"""
    global run_mode_config
    return jsonify({
        'success': True,
        'mode_config': run_mode_config
    })

@app.route('/api/run_mode/update', methods=['POST'])
def update_run_mode():
    """更新运行模式配置"""
    global run_mode_config
    try:
        data = request.json
        
        # 更新配置
        if 'mode' in data:
            valid_modes = ['manual', 'full_day', 'custom']
            if data['mode'] not in valid_modes:
                return jsonify({'success': False, 'message': f'无效的运行模式，可选值：{valid_modes}'})
            run_mode_config['mode'] = data['mode']
        
        if 'full_day' in data:
            run_mode_config['full_day'].update(data['full_day'])
        
        if 'custom' in data:
            run_mode_config['custom'].update(data['custom'])
        
        # 保存配置
        if not save_run_mode_config(run_mode_config):
            return jsonify({'success': False, 'message': '保存配置失败'})
        
        # 如果是全天模式或自定义模式，启动自动运行监控
        start_run_mode_monitor()
        
        return jsonify({
            'success': True,
            'message': '运行模式已更新',
            'mode_config': run_mode_config
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# 自动运行模式监控线程
run_mode_monitor_thread = None
run_mode_monitor_stop_event = threading.Event()

# 检查当前时间是否在指定的时段内
def is_time_in_range(current_time, start_time_str, end_time_str):
    start_hour, start_minute = map(int, start_time_str.split(':'))
    end_hour, end_minute = map(int, end_time_str.split(':'))
    
    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)
    
    # 如果结束时间小于开始时间，说明跨天了
    if end_time < start_time:
        return current_time >= start_time or current_time <= end_time
    else:
        return start_time <= current_time <= end_time

# 运行模式监控函数
def run_mode_monitor():
    global current_assistant, recording_status
    
    while not run_mode_monitor_stop_event.is_set():
        try:
            if run_mode_config['mode'] == 'manual':
                # 手动模式，不自动执行
                time.sleep(60)  # 每分钟检查一次
                continue
            
            current_time = datetime.datetime.now().time()
            today = datetime.datetime.now().date()
            
            # 检查是否正在录音
            is_recording = recording_status.get('is_recording', False)
            
            if run_mode_config['mode'] == 'full_day':
                # 全天模式：10:00-12:30, 13:30-21:00
                config = run_mode_config['full_day']
                
                # 检查是否在上午时段内
                in_morning_period = is_time_in_range(
                    current_time, 
                    config['morning_start'], 
                    config['morning_end']
                )
                
                # 检查是否在下午时段内
                in_afternoon_period = is_time_in_range(
                    current_time, 
                    config['afternoon_start'], 
                    config['afternoon_end']
                )
                
                should_record = in_morning_period or in_afternoon_period
                
            elif run_mode_config['mode'] == 'custom':
                # 自定义模式：检查是否在任何自定义时段内
                should_record = False
                for period in run_mode_config['custom']['periods']:
                    if 'start' in period and 'end' in period:
                        if is_time_in_range(current_time, period['start'], period['end']):
                            should_record = True
                            break
            
            # 根据检查结果控制录音
            if should_record and not is_recording:
                # 应该录音但未录音，开始录音
                print(f"[{datetime.datetime.now()}] 自动开始录音 - 运行模式: {run_mode_config['mode']}")
                
                try:
                    current_assistant = MeetingAssistant()
                    if current_assistant.create_realtime_task() and current_assistant.start_recording():
                        recording_status = {
                            'is_recording': True,
                            'task_id': current_assistant.task_id,
                            'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'end_time': '',
                            'output_file': current_assistant.output_file
                        }
                except Exception as e:
                    print(f"自动开始录音失败: {str(e)}")
            
            elif not should_record and is_recording:
                # 不应该录音但正在录音，停止录音
                print(f"[{datetime.datetime.now()}] 自动停止录音 - 运行模式: {run_mode_config['mode']}")
                
                try:
                    if current_assistant and recording_status['is_recording']:
                        current_assistant.stop_recording()
                        recording_status['is_recording'] = False
                        recording_status['end_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"自动停止录音失败: {str(e)}")
            
            # 每分钟检查一次
            time.sleep(60)
            
        except Exception as e:
            print(f"运行模式监控出错: {str(e)}")
            time.sleep(60)

# 启动运行模式监控
def start_run_mode_monitor():
    global run_mode_monitor_thread, run_mode_monitor_stop_event
    
    # 停止之前的监控线程
    if run_mode_monitor_thread and run_mode_monitor_thread.is_alive():
        run_mode_monitor_stop_event.set()
        run_mode_monitor_thread.join(timeout=5)
        
    # 如果当前模式不是手动模式，启动新的监控线程
    if run_mode_config['mode'] != 'manual':
        run_mode_monitor_stop_event.clear()
        run_mode_monitor_thread = threading.Thread(target=run_mode_monitor)
        run_mode_monitor_thread.daemon = True
        run_mode_monitor_thread.start()
        print(f"启动运行模式监控 - 当前模式: {run_mode_config['mode']}")

@app.route('/api/recording_history', methods=['GET'])
def get_recording_history():
    """获取历史录音记录，支持按日期等条件筛选"""
    global recording_history
    try:
        # 获取查询参数
        date = request.args.get('date')
        search_text = request.args.get('search_text', '').lower()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # 复制历史记录用于筛选
        filtered_history = recording_history.copy()
        
        # 按日期筛选
        if date:
            filtered_history = [record for record in filtered_history if record['date'] == date]
        
        # 按搜索文本筛选
        if search_text:
            filtered_history = [
                record for record in filtered_history 
                if search_text in record['id'].lower() or 
                   search_text in record['start_time'].lower() or
                   search_text in record['output_file'].lower()
            ]
        
        # 分页
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_history = filtered_history[start_index:end_index]
        
        # 为每条记录添加文件信息
        for record in paginated_history:
            try:
                # 从开始时间提取日期
                if record.get('start_time'):
                    date_str = record['start_time'].split(' ')[0] if ' ' in record['start_time'] else record['start_time']
                    folder_path = os.path.join(RESULTS_ROOT_DIR, date_str)
                    
                    # 查找与任务ID或文件名相关的所有文件
                    if os.path.exists(folder_path):
                        files = []
                        # 提取任务ID或文件前缀
                        file_pattern = re.compile(r'会议记录_(\d{8}_\d{6})\.txt')
                        match = file_pattern.match(record.get('output_file', ''))
                        timestamp = match.group(1) if match else ''
                        
                        for f in os.listdir(folder_path):
                            # 检查文件名是否包含相同的时间戳或任务ID
                            if timestamp and timestamp in f:
                                file_path = os.path.join(folder_path, f)
                                files.append({
                                    'name': f,
                                    'size': os.path.getsize(file_path),
                                    'path': os.path.relpath(file_path, RESULTS_ROOT_DIR)
                                })
                        
                        record['files'] = files
            except Exception as e:
                print(f"获取文件信息时出错: {str(e)}")
                record['files'] = []
        
        # 返回结果
        return jsonify({
            'success': True,
            'total': len(filtered_history),
            'page': page,
            'page_size': page_size,
            'records': paginated_history
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取历史记录失败: {str(e)}'})

@app.route('/api/download_file', methods=['GET'])
def download_file():
    """下载历史录音结果文件"""
    try:
        # 获取文件相对路径
        file_path = request.args.get('file_path')
        if not file_path:
            return jsonify({'success': False, 'message': '文件路径不能为空'})
        
        # 构建完整的文件路径
        full_file_path = os.path.join(RESULTS_ROOT_DIR, file_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_file_path):
            return jsonify({'success': False, 'message': '文件不存在'})
        
        # 发送文件
        return send_file(full_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载文件时发生错误: {str(e)}'})

@app.route('/api/view_file', methods=['GET'])
def view_file():
    """查看历史录音结果文件内容"""
    try:
        # 获取文件相对路径
        file_path = request.args.get('file_path')
        if not file_path:
            return jsonify({'success': False, 'message': '文件路径不能为空'})
        
        # 构建完整的文件路径
        full_file_path = os.path.join(RESULTS_ROOT_DIR, file_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_file_path):
            return jsonify({'success': False, 'message': '文件不存在'})
        
        # 读取文件内容
        file_content = ''
        file_ext = os.path.splitext(full_file_path)[1].lower()
        
        if file_ext in ['.txt', '.json']:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        else:
            # 对于不支持直接查看的文件，返回提示信息
            return jsonify({
                'success': True,
                'file_name': os.path.basename(full_file_path),
                'content': '该文件类型不支持直接查看，请下载后查看',
                'file_type': 'binary'
            })
        
        return jsonify({
            'success': True,
            'file_name': os.path.basename(full_file_path),
            'content': file_content,
            'file_type': 'text'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'查看文件时发生错误: {str(e)}'})

if __name__ == '__main__':
    # 确保templates目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # 启动运行模式监控（如果不是手动模式）
    start_run_mode_monitor()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True)