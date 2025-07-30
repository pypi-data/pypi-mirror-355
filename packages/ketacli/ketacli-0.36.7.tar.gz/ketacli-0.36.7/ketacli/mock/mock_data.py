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

from ketacli.sdk.util import Template, format_bytes
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


def process_batch_data(batch_data, query_params, gzip, progress, task_id):
    """
    Process a batch of pre-loaded data and upload them to the server.
    :param batch_data: List of data lines to process.
    :param query_params: Query parameters for the upload.
    :param gzip: Whether to use gzip for the request.
    :param progress: Shared progress object.
    :param task_id: Task ID for tracking progress.
    :return: Tuple of data length and response.
    """
    if not batch_data:
        progress[task_id] += len(batch_data) if batch_data else 0
        return 0, None
    
    data_length = 0
    local_datas = []
    
    # 合并处理：遍历批量数据，同时进行JSON解析和模板渲染
    try:
        for line in batch_data:
            if not line:  # 确保行不为空
                continue
            data_length += len(line)
            try:
                local_datas.append(json.loads(line))
            except Exception as e:
                print(f"Error parsing line: {line}, error: {str(e)}")
                # 跳过错误的行，继续处理
                continue
                
    except Exception as e:
        print(f"Error processing batch data: {str(e)}")
        progress[task_id] += len(batch_data)
        return 0, None
    
    # 如果没有解析到有效数据，直接返回
    if not local_datas:
        progress[task_id] += len(batch_data)
        return 0, None
    
    # 发送到服务端
    response = None
    if local_datas:
        response = request_post("data", local_datas, query_params, gzip=gzip).json()
    
    # 更新进度条
    progress[task_id] += len(batch_data)
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
                    json_strings = [json_serializer.dumps(item) for item in local_datas]
                    serialized_batch = '\n'.join(json_strings)
                    # 一次性写入所有数据
                    f.write(serialized_batch)
                    f.write('\n')  # 确保最后一行也有换行符
                response = {"total": data_length, "success": data_length, "failure": 0}
            except Exception as e:
                response = {"total": data_length, "success": 0, "failure": data_length}

    # 释放内存
    del rendered_texts
    del local_datas
    
    # 更新进度条
    progress[task_id] += count
    return data_length, response


def handle_generate_to_server(repo, data, number, batch, gzip, workers, render):
    """
    场景1: 生成日志并发送到服务端
    """
    query_params = {"repo": repo}
    
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
        task = prog.add_task("Generating and sending to server...", total=number)

        # 使用上下文管理器确保资源正确释放
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = []
            
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

            # 提交任务
            for worker_id in sorted(tasks_by_worker.keys()):
                for task_info in tasks_by_worker[worker_id]:
                    futures.append(
                        executor.submit(
                            generate_and_upload, 
                            data, 
                            task_info["batch_size"], 
                            query_params, 
                            gzip, 
                            progress, 
                            task_info["task_id"],
                            "server", 
                            None,
                            None,
                            render
                        )
                    )            
            
            return _collect_results(futures, progress, number, prog, task)


def handle_generate_to_file(data, number, batch, workers, output_file, render):
    """
    场景2: 生成日志并写文件
    """
    # 如果是文件输出模式，初始化文件
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        # 如果是单进程模式，直接初始化输出文件
        if workers is None or workers <= 1:
            with open(output_file, 'w', encoding='utf-8', buffering=32768) as f:
                pass  # 只创建/清空文件，不写入内容
    except Exception as e:
        console.print(f"Error creating output file: {str(e)}")
        return None, []
    
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
        task = prog.add_task("Generating and writing to file...", total=number)

        # 使用上下文管理器确保资源正确释放
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = []
            
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

            # 提交任务
            for worker_id in sorted(tasks_by_worker.keys()):
                for task_info in tasks_by_worker[worker_id]:
                    futures.append(
                        executor.submit(
                            generate_and_upload, 
                            data, 
                            task_info["batch_size"], 
                            None,  # 文件模式不需要query_params
                            False,  # 文件模式不需要gzip
                            progress, 
                            task_info["task_id"],
                            "file", 
                            output_file,
                            task_info["worker_id"] if workers > 1 else None,
                            render
                        )
                    )
            return _collect_results(futures, progress, number, prog, task)



def handle_file_to_server(repo, file_path, number, batch, gzip, workers):
    """
    场景3: 读文件并发送到服务端
    """
    query_params = {"repo": repo}
    
    # 预读取文件内容到内存（优化：避免多次文件IO）
    file_lines = []
    try:
        with open(file_path, encoding="utf8") as f:
            for line in f:
                line = line.strip().replace("}{", "}\n{").split("\n")[0]
                if line:
                    file_lines.append(line)
    except Exception as e:
        console.print(f"Error reading file {file_path}: {str(e)}")
        return None, []
    
    total_lines = len(file_lines)
    if total_lines == 0:
        console.print("File is empty")
        return None, []
    
    # 如果没有指定number，则处理文件中的所有行
    if not number:
        number = total_lines
        console.print(f"Processing all {number} lines from file {file_path}")
    elif number <= total_lines:
        console.print(f"Processing {number} lines from file {file_path}")
    else:
        console.print(f"Processing {number} lines from file {file_path} (file has {total_lines} lines, will repeat)")
    
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
        task = prog.add_task(f"[green][{workers}]workers[/green]: Reading file and sending to server... ", total=number)

        # 使用上下文管理器确保资源正确释放
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = []
            
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

            # 提交任务
            for worker_id in sorted(tasks_by_worker.keys()):
                for task_info in tasks_by_worker[worker_id]:
                   
                    
                    # 计算当前批次在文件中的起始行
                    start_line = sum(t["batch_size"] for w in range(worker_id) for t in tasks_by_worker.get(w, []))
                    start_line += sum(t["batch_size"] for t in tasks_by_worker[worker_id] if t["task_id"] == task_info["task_id"] and tasks_by_worker[worker_id].index(t) < tasks_by_worker[worker_id].index(task_info))
                    
                    # 准备当前批次的数据
                    batch_data = []
                    for i in range(task_info["batch_size"]):
                        line_index = (start_line + i) % len(file_lines)
                        batch_data.append(file_lines[line_index])
                    
                    # 提交任务，使用预处理的数据
                    futures.append(
                        executor.submit(
                            process_batch_data,
                            batch_data,
                            query_params,
                            gzip,
                            progress,
                            task_info["task_id"]
                        )
                    )

            return _collect_results(futures, progress, number, prog, task)


def _collect_results(futures, progress, number, prog, task):
    """
    收集任务结果的通用函数
    """
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
                
                responses.append(resp)
                    
                # 收集临时文件信息
                if isinstance(resp, dict) and 'temp_file' in resp:
                    temp_files.add(resp['temp_file'])
        except Exception as e:
            console.print(f"Task failed: {str(e)}")
    
    return total_data_length, responses, temp_files


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

    # 输入验证
    if repo is None:
        console.print(f"Please specify target repo with --repo")
        return

    if data is None and file is None:
        console.print(f"Please use --data or --file to specify data to upload")
        return

    if file and not os.path.exists(file):
        console.print(f"Error: file {file} does not exist")
        return

    if output_type == 'file' and not output_file:
        console.print("Error: output_file is required when output_type is 'file'")
        return

    if file is not None and output_type != 'server':
        console.print("When using file parameter, output_type can only be 'server'")
        return

    # 根据参数组合确定处理场景并调用对应的处理函数
    try:
        if file:
            # ketacli mock_log --render -n 1000000 --batch 2000  --worker 32 --file test.log --repo benchmark_write_parallel_27_replica_2
            # 场景3: 读文件并发送到服务端
            total_data_length, responses, _ = handle_file_to_server(
                repo, file, number, batch, gzip, workers
            )
        elif output_type == "server":
            # ketacli mock_log --render -n 1000000 --batch 2000  --worker 32 --repo benchmark_write_parallel_27_replica_2
            # 场景1: 生成日志并发送到服务端
            total_data_length, responses, _ = handle_generate_to_server(
                repo, data, number, batch, gzip, workers, render
            )
        elif output_type == "file":
            # 场景2: 生成日志并写文件
            # ketacli mock_log --render -n 1000000 --batch 2000  --worker 32 --repo benchmark_write_parallel_27_replica_2 --output_type file --output_file test.log
            total_data_length, responses, temp_files = handle_generate_to_file(
                data, number, batch, workers, output_file, render
            )
            if workers > 1 and temp_files:
                try:
                    merge_start = time.time()
                    console.print(f"Starting to merge {len(temp_files)} temporary files...")
                    
                    # 合并所有临时文件到最终输出文件
                    with open(output_file, 'w', encoding='utf-8', buffering=32768) as outfile:
                        for temp_file in sorted(temp_files):
                            if os.path.exists(temp_file):
                                with open(temp_file, 'r', encoding='utf-8', buffering=32768) as infile:
                                    shutil.copyfileobj(infile, outfile, 1024*1024)  # 1MB块大小
                            # 删除临时文件
                            os.remove(temp_file)
                
                    merge_duration = time.time() - merge_start
                    console.print(f"Successfully merged {len(temp_files)} temporary files into {output_file} in {merge_duration:.2f} seconds")
                except Exception as e:
                    console.print(f"Error merging files: {str(e)}")
        else:
            console.print(f"Error: unsupported output_type '{output_type}'")
            return

        # 临时文件合并逻辑已移动到 handle_generate_to_file 方法中

        # 显示结果摘要
        if output_type == "server" or file:
            if responses:
                success_count = sum(r['success'] for r in responses)
                total_count = sum(r['total'] for r in responses)
                console.print(f"Successfully uploaded: {success_count}/{total_count} batches")
            
            
            console.print(f"Total: {format_bytes(total_data_length)}")
        else:
            console.print(f"Data written to {output_file}")
            console.print(f"Total: {format_bytes(total_data_length)} bytes")
            
        console.print(f'Total Duration: {time.time() - start:.2f} seconds')
        console.print(f'速度: {number/(time.time() - start):.2f} 条/s')

    except Exception as e:
        console.print(f"Error during processing: {str(e)}")
        return


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