import time
import json
import os
import math
import multiprocessing
import tempfile
import random
import shutil
import socket
import struct
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from rich.progress import Progress
from rich.console import Console
from mando import command, arg

from ketacli.sdk.util import Template
from ketacli.sdk.base.client import request_post

from ketacli.mock.log_generator import LogGenerator

# 尝试导入ujson，如果不可用则使用标准json
try:
    import ujson as json_serializer
    USE_UJSON = True
except ImportError:
    import json as json_serializer
    USE_UJSON = False

# 创建控制台对象
console = Console()

 # 使用LogGenerator类生成日志
        
        
# 创建日志生成器实例
log_generator = LogGenerator()


def process_file_batch(file_path, start_line, count, query_params, gzip, progress, task_id):
    """
    Process a batch of lines from a file and upload them to the server.
    :param file_path: Path to the file containing data.
    :param start_line: Starting line index (0-based).
    :param count: Number of lines to process.
    :param query_params: Query parameters for the upload.
    :param gzip: Whether to use gzip for the request.
    :param progress: Shared progress object.
    :param task_id: Task ID for tracking progress.
    :return: Tuple of data length and response.
    """
    # 读取指定范围的行
    lines = []
    data_length = 0
    
    # 首先计算文件总行数
    with open(file_path, 'r', encoding='utf8') as f:
        total_lines = sum(1 for _ in f)
    
    # 如果文件为空，直接返回
    if total_lines == 0:
        progress[task_id] += count
        return 0, None
    
    # 计算实际的起始行（考虑文件循环）
    actual_start_line = start_line % total_lines
    
    # 读取指定数量的行，如果文件行数不足，则循环读取
    remaining_count = count
    
    while remaining_count > 0:
        with open(file_path, 'r', encoding='utf8') as f:
            # 跳过前面的行
            for _ in range(actual_start_line):
                next(f, None)
            
            # 读取行直到文件结束或达到所需数量
            while remaining_count > 0:
                line = next(f, None)
                if line is None:  # 文件结束
                    break
                line = line.strip()
                if line:  # 忽略空行
                    lines.append(line)
                    data_length += len(line)
                    remaining_count -= 1
        
        # 如果还需要更多行，则从文件开头继续读取
        actual_start_line = 0
    
    # 如果没有读取到数据，直接返回
    if not lines:
        progress[task_id] += count
        return 0, None
    
    # 解析JSON数据
    local_datas = []
    for line in lines:
        try:
            local_datas.append(json.loads(line))
        except Exception as e:
            print(f"Error parsing line: {line}, error: {str(e)}")
            # 跳过错误的行，继续处理
            continue
    
    # 发送到服务端
    response = None
    if local_datas:
        response = request_post("data", local_datas, query_params, gzip=gzip).json()
    
    # 更新进度条
    progress[task_id] += count
    return data_length, response


def generate_and_upload(data, count, query_params, gzip, progress, task_id, output_type='server', output_file=None, worker_id=None, render=True):
    """
    Generate mock data and upload in a batch.
    :param data: The JSON string template.
    :param count: Number of data items to generate.
    :param query_params: Query parameters for the upload.
    :param gzip: Whether to use gzip for the request.
    :param progress: Shared progress object.
    :param task_id: Task ID for tracking progress.
    :param output_type: Where to write the data, 'server' or 'file'.
    :param output_file: File path to write data when output_type is 'file'.
    :param worker_id: Worker ID for creating worker-specific temp files.
    :return: Tuple of data length and response.
    """
    # # 创建一次Template对象，避免重复创建
    temp = Template(data)
    
    # # 使用批量渲染功能一次性生成所有数据
    rendered_texts = temp.batch_render(count, render=render)
    
    # 直接计算数据长度，避免额外的迭代
    data_length = sum(len(text) for text in rendered_texts)
    
    # 预分配列表大小以避免动态扩展
    local_datas = [None] * count
    
    # 批量解析JSON - 使用分块处理以提高性能
    CHUNK_SIZE = 5000  # 每次处理的数据量
    for i in range(0, count, CHUNK_SIZE):
        chunk = rendered_texts[i:i+CHUNK_SIZE]
        # 使用列表推导式批量解析JSON并直接赋值
        parsed_chunk = [json.loads(text) for text in chunk]
        # 将解析结果放入预分配的列表中
        for j, item in enumerate(parsed_chunk):
            local_datas[i+j] = item

    response = None
    if local_datas:
        if output_type == 'server':
            # 发送到服务端
            response = request_post("data", local_datas, query_params, gzip=gzip).json()
        elif output_type == 'file' and output_file:
            # 确定写入的文件路径
            # 如果是多进程模式，每个进程写入自己的临时文件
            actual_output_file = output_file
            if worker_id is not None:
                # 创建临时文件，使用worker_id作为文件名的一部分
                temp_dir = os.path.dirname(os.path.abspath(output_file))
                file_name = os.path.basename(output_file)
                base_name, ext = os.path.splitext(file_name)
                actual_output_file = os.path.join(temp_dir, f"{base_name}_temp_{worker_id}{ext}")
            
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(os.path.abspath(actual_output_file)), exist_ok=True)
                
                # 使用更大的缓冲区和批量写入
                with open(actual_output_file, 'a', encoding='utf-8', buffering=32768) as f:
                    # 批量序列化和写入，减少IO操作
                    BATCH_SIZE = count  # 增加每批处理的记录数
                    for i in range(0, len(local_datas), BATCH_SIZE):
                        batch = local_datas[i:i+BATCH_SIZE]
                        # 使用列表推导式一次性生成所有JSON字符串
                        # 使用列表推导式而不是生成器表达式，避免额外的迭代开销
                        json_strings = [json_serializer.dumps(item) for item in batch]
                        serialized_batch = '\n'.join(json_strings)
                        # 一次性写入整批数据
                        f.write(serialized_batch)
                        f.write('\n')  # 确保最后一行也有换行符
                        
                response = {"status": "success", "message": f"Data written to {actual_output_file}", "temp_file": actual_output_file}
            except Exception as e:
                response = {"status": "error", "message": str(e)}

    # 释放内存
    del rendered_texts
    del local_datas
    
    # 更新进度条
    progress[task_id] += count
    return data_length, response


@command
def mock_data(repo="default", data=None, file=None, number:int=1, batch:int=2000, gzip=False, workers:int=1, output_type="server", output_file=None, render=False):
    """
    Mock data to specified repo

    :param --repo: The target repo, default: "default"
    :param --data: The json string data default: {"raw":"{{ faker.sentence() }}", "host": "{{ faker.ipv4_private() }}"}
    :param --file: Upload json text from file path.
    :param --number,-n: Number of data, default 1
    :param --worker: for worker process configs like quantity.
    :param --gzip: a boolean for enabling gzip compression.
    :param --batch: to set batch processing size or related configs.
    :param --output_type: Where to write the data, 'server' or 'file', default: 'server'
    :param --output_file: File path to write data when output_type is 'file'
    :param --render: Whether to render the template, default: False. When set to False, it will skip template rendering and use raw text directly, which can improve performance for simple text data.

    
    """
    start = time.time()
    if workers:
        workers = int(workers)
    if batch:
        batch = int(batch)

    if repo is None:
        console.print(f"Please specify target repo with --repo")
        return

    if data is None and file is None:
        console.print(f"Please use --data or --file to specify data to upload")
        return

    if file is not None:
        # 当从文件读取数据时，output_type 只能为 server
        if output_type != 'server':
            console.print("When using file parameter, output_type can only be 'server'")
            return
        
        # 从文件中读取数据，但不一次性加载到内存
        with open(file, encoding="utf8") as f:
            # 只读取文件的第一行来获取数据格式
            first_line = f.readline().strip()
            if first_line:
                data = first_line
            else:
                console.print("File is empty")
                return

    # 准备查询参数
    query_params = {"repo": repo}

    # 处理文件输入模式
    if file is not None:
        # 计算文件总行数
        with open(file, encoding="utf8") as f:
            total_lines = sum(1 for _ in f)
        
        if total_lines == 0:
            console.print("File is empty")
            return
        
        # 如果指定了number参数
        if number:
            if number < total_lines:
                # 限制处理的行数
                total_lines = number
                console.print(f"Processing {number} lines from file {file}")
            else:
                # 当number大于total_lines时，需要重复读取文件数据
                repeat_times = math.ceil(number / total_lines)
                console.print(f"Processing {number} lines from file {file} (repeating file content {repeat_times} times)")
        else:
            # 使用文件行数作为总数
            number = total_lines
            console.print(f"Processing {number} lines from file {file}")
    
    # 如果是文件输出模式，初始化文件
    if output_type == 'file' and output_file:
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            # 如果是单进程模式，直接初始化输出文件
            if workers is None or workers <= 1:
                with open(output_file, 'w', encoding='utf-8', buffering=32768) as f:
                    pass  # 只创建/清空文件，不写入内容
        except Exception as e:
            console.print(f"Error creating output file: {str(e)}")
            return
    
    # 确保workers至少为1
    workers = max(1, workers)
    
    # 计算每个工作进程处理的项目数
    items_per_worker = math.ceil(number / workers)
    
    # 共享进度管理
    manager = Manager()
    progress = manager.dict()
    task_ids = []

    # 创建任务列表，均匀分配任务
    remaining_count = number
    
    # 初始化进度条任务
    with Progress(console=console) as prog:
        task = prog.add_task("Mocking Data...", total=number)

        # 使用上下文管理器确保资源正确释放
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            # 为每个工作进程创建任务 - 修改为一次性提交所有工作进程的所有任务
            worker_tasks = []
            
            # 准备所有工作进程的任务并直接按工作进程分组
            tasks_by_worker = {}
            for i in range(workers):
                # 计算当前工作进程的项目数
                worker_count = min(items_per_worker, remaining_count)
                if worker_count <= 0:
                    break
                    
                # 计算当前工作进程的批次数和最后一个批次的大小
                full_batches = worker_count // batch
                last_batch_size = worker_count % batch
                
                # 初始化进度
                task_id = f"worker_{i}"
                task_ids.append(task_id)
                progress[task_id] = 0
                
                # 初始化当前工作进程的任务列表
                tasks_by_worker[i] = []
                
                # 准备完整批次的任务
                for j in range(full_batches):
                    tasks_by_worker[i].append({
                        "worker_id": i,
                        "task_id": task_id,
                        "batch_size": batch,
                        "is_last_batch": False
                    })
                
                # 准备最后一个不完整批次（如果有）
                if last_batch_size > 0:
                    tasks_by_worker[i].append({
                        "worker_id": i,
                        "task_id": task_id,
                        "batch_size": last_batch_size,
                        "is_last_batch": True
                    })
                    
                # 更新剩余项目数
                remaining_count -= worker_count

            
            # 然后提交剩余的任务
            for worker_id in sorted(tasks_by_worker.keys()):
                for task_info in tasks_by_worker[worker_id]:
                    # 如果是从文件读取数据，则需要特殊处理
                    if file is not None:
                        # 计算当前批次在文件中的起始行和结束行
                        start_line = sum(t["batch_size"] for w in range(worker_id) for t in tasks_by_worker.get(w, []))
                        start_line += sum(t["batch_size"] for t in tasks_by_worker[worker_id] if t["task_id"] == task_info["task_id"] and tasks_by_worker[worker_id].index(t) < tasks_by_worker[worker_id].index(task_info))
                        
                        # 提交任务，使用特殊的文件批处理模式
                        futures.append(
                            executor.submit(
                                process_file_batch,
                                file,
                                start_line,
                                task_info["batch_size"],
                                query_params,
                                gzip,
                                progress,
                                task_info["task_id"]
                            )
                        )
                    else:
                        # 正常的数据生成和上传
                        futures.append(
                            executor.submit(
                                generate_and_upload, 
                                data, 
                                task_info["batch_size"], 
                                query_params, 
                                gzip, 
                                progress, 
                                task_info["task_id"],
                                output_type, 
                                output_file,
                                task_info["worker_id"] if output_type == 'file' and workers > 0 else None,  # 传递worker_id用于创建临时文件
                                render
                            )
                        )

            total_data_length = 0
            responses = []
            temp_files = set()

            # 收集结果并更新进度
            completed = 0
            while completed < number:
                # 计算已完成的项目数
                current_completed = sum(progress.values())
                if current_completed > completed:
                    # 更新进度条
                    prog.update(task, advance=current_completed - completed)
                    completed = current_completed
                
                # 短暂休眠以减少CPU使用
                time.sleep(0.1)
                
                # 检查是否所有任务都已完成
                if all(future.done() for future in futures):
                    # 确保进度条显示100%
                    final_completed = sum(progress.values())
                    if final_completed > completed:
                        prog.update(task, advance=final_completed - completed)
                    break
            
            # 收集结果
            for future in futures:
                try:
                    data_length, resp = future.result()
                    total_data_length += data_length
                    if resp:
                        if resp not in responses:
                            responses.append(resp)
                        # 收集临时文件路径
                        if output_type == 'file' and 'temp_file' in resp:
                            temp_files.add(resp['temp_file'])
                except Exception as e:
                    console.print(f"Error processing future: {str(e)}")

            # 清理资源
            futures.clear()
            
            # 修改合并文件部分，添加更详细的日志输出
            # 如果是文件输出模式且有多个进程，合并临时文件
            if output_type == 'file' and output_file and len(temp_files) > 0:
                try:
                    merge_start = time.time()
                    console.print(f"Starting to merge {len(temp_files)} temporary files...")
                    
                    # 创建或清空最终输出文件
                    with open(output_file, 'w', encoding='utf-8') as f:
                        pass
                    
                    # 合并所有临时文件到最终输出文件
                    with open(output_file, 'a', encoding='utf-8', buffering=32768) as outfile:
                        # 添加合并进度任务
                        merge_task = prog.add_task("Merging files...", total=len(temp_files))
                        
                        for i, temp_file in enumerate(temp_files):
                            if os.path.exists(temp_file):
                                with open(temp_file, 'r', encoding='utf-8', buffering=32768) as infile:
                                    # 使用大块读取和写入以提高性能
                                    shutil.copyfileobj(infile, outfile, 1024*1024)  # 1MB块大小
                                # 删除临时文件
                                os.remove(temp_file)
                            prog.update(merge_task, advance=1)
                    
                    merge_duration = time.time() - merge_start
                    console.print(f"Successfully merged {len(temp_files)} temporary files into {output_file} in {merge_duration:.2f} seconds")
                except Exception as e:
                    console.print(f"Error merging files: {str(e)}")

    # 显示结果摘要而不是完整响应，减少输出量
    if output_type == "server":
        success_count = sum(1 for r in responses if r and r.get("status") == "success")
        console.print(f"Successfully uploaded: {success_count}/{len(responses)} batches")
    else:
        console.print(f"Data written to {output_file}")
        
    console.print(f"Total: {total_data_length} bytes")
    console.print(f'Total Duration: {time.time() - start:.2f} seconds')
    console.print(f'速度: {number/(time.time() - start):.2f} 条/s')

    # 清理资源
    futures = None
    responses.clear()
    progress.clear()
    task_ids.clear()


@command
@arg("log_type", type=str,
     completer=lambda prefix, **kwd: [x for x in log_generator.get_supported_log_types() if
                                      x.startswith(prefix)])
def mock_log(repo="default", data=None, file=None, number=1, batch=2000, gzip=False, workers=1, output_type="server", output_file=None, render=False, log_type="nginx"):
    """Mock log data to specified repo, with multiple log types support
    :param --repo: The target repo, default: "default"
    :param --data: The json string data default:
        {
            "raw": "{{ faker.sentence(nb_words=10) }}",
            "host": "{{ faker.ipv4_private() }}"
        }
    :param --file: Upload json text from file path.
    :param --number,-n: Number of data, default 1
    :param --output_type: Where to write the data, 'server' or 'file', default: 'server'
    :param --output_file: File path to write data when output_type is 'file'
    :param --render: Whether to render the template, default: False. When set to False, it will skip template rendering and use raw text directly, which can improve performance for simple text data.
    :param --log_type: Type of log to generate, options: 'nginx', 'java', 'linux', default: 'nginx'
    """
    if not data:
       
        
        try:
            # 生成指定类型的日志
            data = log_generator.generate_log(log_type, render)
        except ValueError as e:
            console.print(f"[red]{str(e)}[/red]")
            return
        
    # 直接调用优化后的mock_data函数
    mock_data(repo, data, file, number, batch, gzip, workers, output_type, output_file, render)


@command
def mock_metrics(repo="metrics_keta", data=None, file=None, number=1, batch=2000, gzip=False, workers=1, output_type="server", output_file=None, render=False):
    """Mock metrics data to specified repo
    :param --repo: The target repo, default: "metrics_keta"
    :param --data: The json string data default:
        {
            "host": "{{ faker.ipv4_private() }}",
            "region": "{{ random.choice(['us-west-2', 'ap-shanghai', 'ap-nanjing', 'ap-guangzhou']) }}",
            "os": "{{ random.choice(['Ubuntu', 'Centos', 'Debian', 'TencentOS']) }}",
            "timestamp": {{ int(time.time() * 1000) }},
            "fields": {
                "redis_uptime_in_seconds": {{ random.randint(1,1000000) }},
                "redis_total_connections_received": {{ random.randint(1,1000000) }},
                "redis_expired_keys": {{ random.randint(1,1000000) }}
            }
        }
    :param --file: Upload json text from file path.
    :param --number,-n: Number of data, default 1
    :param --output_type: Where to write the data, 'server' or 'file', default: 'server'
    :param --output_file: File path to write data when output_type is 'file'
    :param --render: Whether to render the template, default: False. When set to False, it will skip template rendering and use raw text directly, which can improve performance for simple text data.

    """
    if not data:
        # 使用更紧凑的JSON格式，减少解析开销
        if render:
            data = (
                '{"host":"{{ faker.ipv4_private() }}",'
                '"region":"{{ random.choice([\"us-west-2\",\"ap-shanghai\",\"ap-nanjing\",\"ap-guangzhou\"]) }}",'
                '"os":"{{ random.choice([\"Ubuntu\",\"Centos\",\"Debian\",\"TencentOS\"]) }}",'
                '"timestamp":{{ int(time.time() * 1000) }},'
                '"fields":{'
                '"redis_uptime_in_seconds":{{ random.randint(1,1000000) }},'
                '"redis_total_connections_received":{{ random.randint(1,1000000) }},'
                '"redis_expired_keys":{{ random.randint(1,1000000) }}'
                '}}'
            )
        else:
            # 当render为false时，使用f-string直接生成数据，避免模板渲染开销
            regions = ["us-west-2", "ap-shanghai", "ap-nanjing", "ap-guangzhou"]
            os_types = ["Ubuntu", "Centos", "Debian", "TencentOS"]
            data = (
                f'{{"host":"{socket.inet_ntoa(struct.pack("!I", random.randint(0xc0a80001, 0xc0a8ffff)))}",'
                f'"region":"{random.choice(regions)}",'
                f'"os":"{random.choice(os_types)}",'
                f'"timestamp":{int(time.time() * 1000)},'
                f'"fields":{{'
                f'"redis_uptime_in_seconds":{random.randint(1,1000000)},'
                f'"redis_total_connections_received":{random.randint(1,1000000)},'
                f'"redis_expired_keys":{random.randint(1,1000000)}'
                f'}}}}'
            )
    # 直接调用优化后的mock_data函数
    mock_data(repo, data, file, number, batch, gzip, workers, output_type, output_file, render)