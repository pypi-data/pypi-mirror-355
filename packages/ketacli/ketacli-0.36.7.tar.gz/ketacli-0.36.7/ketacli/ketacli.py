import argcomplete
import importlib.metadata
from mando import command, main, arg
import time
from datetime import datetime
import sys
from ketacli.sdk.base.client import *
from ketacli.sdk.base.search import search_spl, search_spl_meta, search_pql
from ketacli.sdk.request.list import list_assets_request, list_admin_request
from ketacli.sdk.request.create import create_asset_request
from ketacli.sdk.request.get import get_asset_by_id_request
from ketacli.sdk.request.update import update_asset_request
from ketacli.sdk.request.delete import delete_asset_request
from ketacli.sdk.request.export import export_asset_request
from ketacli.sdk.request.asset_map import get_resources
from ketacli.sdk.base.config import *
from ketacli.sdk.output.output import list_output, describe_output, get_asset_output
from ketacli.sdk.output.output import search_result_output
from ketacli.sdk.output.format import format_table
from ketacli.sdk.output.output import rs_output_all, rs_output_one
from ketacli.sdk.util import parse_url_params, Template
from rich.console import Console
from rich.live import Live
from ketacli.sdk.chart.layout import LayoutChart
from pkg_resources import resource_filename
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from rich.progress import Progress

# 导入mock模块中的函数
from ketacli.mock.mock_data import mock_data, mock_log, mock_metrics, generate_and_upload

console = Console()


@command
def login(name="keta", endpoint="http://localhost:9000", token=""):
    """Login to ketadb, cache authentication info to ~/.keta/config.yaml

    :param repository: Repository to push to.
    :param -n, --name: The login account name. Defaults to "keta".
    :param -e, --endpoint: The ketadb endpoint. Defaults to "http://localhost:9000".
    :param -t, --token: Your keta api token, create from ketadb webui. Defaults to "".
    """
    do_login(name=name, endpoint=endpoint, token=token)


@command
@arg("name", type=str,
     completer=lambda prefix, **kwd: [x['name'] for x in list_clusters() if x['name'].startswith(prefix)])
def logout(name=None):
    """Logout from ketadb, clear authentication info

    :param -n, --name: logout from which account
    """
    do_logout(name)


@command('list')
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def _list(asset_type, groupId=-1, order="desc", pageNo=1, pageSize=10, prefix="", sort="updateTime", fields="",
          format=None, raw=False, lang=None, extra=None, watch=False, interval=3.0, show_all_fields=False):
    """List asset (such as repo,sourcetype,metric...) from ketadb

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param -l, --pageSize: Limit the page size.
    :param --pageNo: Limit the page number.
    :param --prefix: Fuzzy query filter.
    :param --sort: The field used to order by
    :param --order: The sort order, desc|asc
    :param --fields: The fields to display. Separate by comman, such as "id,name,type"
    :param -f, --format: The output format, text|json|csv|html|latex
    :param --groupId: The resource group id.
    :param --raw: Prettify the time field or output the raw timestamp, if specified, output the raw format
    :param --lang: Choose the language preference of return value
    :param -e, --extra: extra query filter, example: include_defaults=true,flat_settings=true
    :param -w, --watch: Watch the resource change
    :param --interval: refresh the resource change
    :param -a, --show_all_fields: all fields to display
    """
    extra_dict = {}
    if extra is not None:
        # 解析 url 参数为 dict
        extra_dict = parse_url_params(extra)

    def generate_table():
        req = list_assets_request(
            asset_type, groupId, order, pageNo, pageSize, prefix, sort, lang, **extra_dict)
        resp = request_get(req["path"], req["query_params"],
                           req["custom_headers"]).json()
        output_fields = req.get("default_fields", [])
        if show_all_fields:
            output_fields = []
        if len(fields.strip()) > 0:
            output_fields = fields.strip().split(",")
        table = list_output(asset_type, output_fields=output_fields, resp=resp)
        if not table:
            return None
        return format_table(table, format, not raw)

    if watch:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                try:
                    table = generate_table()
                    live.update(table)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    live.stop()
                    sys.exit()
    else:
        table = generate_table()
        if table is None:
            console.print(f"we cannot find any {asset_type}")
        else:
            console.print(table, overflow="fold")


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
def admin(asset_type, format="json", extra=None, watch=False, interval=3.0):
    """List asset (such as repo,sourcetype,metric...) from ketadb

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param -f, --format: The output format, text|json|csv|html|latex
    :param -e, --extra: extra query filter, example: include_defaults=true,flat_settings=true
    :param -w, --watch: Watch the resource change
    :param --interval: refresh the resource change
    """
    extra_dict = {}
    if extra is not None:
        # 解析 url 参数为 dict
        extra_dict = parse_url_params(extra)

    def generate_table():
        req = list_admin_request(asset_type, **extra_dict)
        resp = request_get(req["path"], req["query_params"], req["custom_headers"]).json()
        output_fields = []
        table = list_output(asset_type, output_fields=output_fields, resp=resp)
        return format_table(table, format)

    if watch:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                try:
                    table = generate_table()
                    live.update(table)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    live.stop()
                    sys.exit()
    else:
        table = generate_table()
        if table is None:
            console.print(f"we cannot find any {asset_type}")
        else:
            console.print(table)


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def get(asset_type, asset_id, fields="", format=None, lang=None, extra=None):
    """Get asset detail info from ketadb

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param asset_id: The unique id of asset. (such as id or name...)
    :param --fields: The fields to display. Separate by comman, such as "id,name,type"
    :param -f, --format: The output format, text|json|csv|html|latex
    :param --lang: Choose the language preference of return value
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    extra_args_map['name'] = asset_id

    req = get_asset_by_id_request(
        asset_type=asset_type, asset_id=asset_id, lang=lang, **extra_args_map)
    resp = request_get(req["path"], req["query_params"],
                       req["custom_headers"]).json()
    if format == "json":
        console.print(json.dumps(resp, indent=2, ensure_ascii=False))
        return

    output_fields = []
    if len(fields.strip()) > 0:
        output_fields = fields.strip().split(",")
    table = get_asset_output(output_fields=output_fields, resp=resp)
    table.align = "l"
    if table is None:
        console.print(f"we cannot find any {asset_type}")
    else:
        console.print(format_table(table, format), overflow="fold")


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def describe(asset_type, format=None):
    """Describe the schema of asset type

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param -f, --format: The output format, text|json|csv|html|latex
    """

    req = list_assets_request(asset_type)
    resp = request_get(req["path"], req["query_params"],
                       req["custom_headers"]).json()
    table = describe_output(asset_type, resp=resp)
    if table is None:
        console.print(f"we cannot find any {asset_type}")
    else:
        console.print(format_table(table, format), overflow="fold")


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
def search(spl, start=None, end=None, limit=100, format=None, raw=False, watch=False, interval=3.0):
    """Search spl from ketadb

    :param spl: The spl query
    :param --start: The start time. Time format "2024-01-02 10:10:10"
    :param --end: The start time. Time format "2024-01-02 10:10:10"
    :param -l, --limit: The limit size of query result
    :param -f, --format: The output format, table|text|json|csv|html|latex
    :param --raw: Prettify the time field or output the raw timestamp, if specified, output the raw format
    :param -w, --watch: Watch the resource change
    :param --interval: refresh the resource change
    """
    if start is not None:
        start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    if end is not None:
        end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

    def generate_table():
        resp = search_spl(spl=spl, start=start, end=end, limit=limit)
        return format_table(search_result_output(resp), format, not raw)

    if watch:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                try:
                    table = generate_table()
                    live.update(table)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    live.stop()
                    sys.exit()

    else:
        table = generate_table()
        if table is None:
            console.print(f"we cannot find any data")
        else:
            console.print(table, overflow="fold")


@command
def benchmark(type="spl", query=None, start: float = 0.0, end: float = None, limit=None, cnt=1, workers=1, base_url="",
              window=0):
    """benchmark spl from ketadb
    :param spl: The spl query
    :param --start: The start time
    :param --end: The start time
    :param -l, --limit: The limit size of query result
    :param -c, --cnt: The count of benchmark
    :param -w, --workers: The count of workers
    :param -b, --base_url: The base url of pql
    :param --window: The window of benchmark
    """

    result = {
        "type": type,
        "query": query,
        "cnt": cnt,
        "results": [],
        "waiting": 0,
        'request_cnt': cnt
    }
    futures = []
    started = time.time()
    if not end:
        end = time.time()
    if isinstance(query, str):
        querys = [query]
    elif isinstance(query, list):
        querys = query
    else:
        raise Exception("query must be str or list")
    with Progress() as progress:
        if window:
            new_cnt = int((end - start) / window) * cnt * len(querys)
            result['request_cnt'] = new_cnt
        else:
            new_cnt = cnt * len(querys)
            result['request_cnt'] = new_cnt
        task = progress.add_task(f"[green]Benchmarking total: {new_cnt}...", total=new_cnt)
        with ProcessPoolExecutor(max_workers=workers) as executor:

            if not window:
                for _ in range(cnt):
                    for query in querys:
                        if type == "spl":
                            futures.append(
                                executor.submit(search_spl_meta, spl=query, start=start, end=end, limit=limit))
                        elif type == "pql":
                            futures.append(
                                executor.submit(search_pql, base_url=base_url, pql=query, start=start, end=end,
                                                limit=limit))
            else:

                while True:
                    new_end = start + window
                    print(datetime.fromtimestamp(start).strftime('%d-%H:%M:%S'),
                          datetime.fromtimestamp(new_end).strftime('%H:%M:%S'), )
                    if new_end > end:
                        break
                    for query in querys:
                        if type == "spl":
                            for _ in range(cnt):
                                futures.append(
                                    executor.submit(search_spl_meta, spl=query, start=start, end=new_end, limit=limit))
                        elif type == "pql":
                            for _ in range(cnt):
                                futures.append(
                                    executor.submit(search_pql, base_url=base_url, pql=query, start=start, end=new_end,
                                                    limit=limit))
                    start += window

            for future in futures:
                resp = future.result()
                result["results"].append(resp)
                result["avg_duration"] = sum([x["duration"] for x in result["results"]]) / len(result["results"])
                progress.update(task, advance=1)
    result["waiting"] = time.time() - started
    result["total_duration"] = round(sum([x["duration"] for x in result["results"] if "duration" in x]))
    result['totalSize'] = sum([x["resultSize"] for x in result["results"] if "resultSize" in x])
    console.print(result)


@command
def benchmark_for_file(type='spl', file_path=None, start=0, end=0, limit=None, cnt=1, workers=1, base_url="",
                       window=0):
    """从文件批量执行性能测试
    通过读取包含多个查询语句的文件，进行批量压力测试

    :param type: 测试类型 spl/pql
    :param file_path: 包含查询语句的文件路径，每行一个查询
    :param start: 测试时间范围起始时间戳
    :param end: 测试时间范围结束时间戳
    :param limit: 单次查询结果限制数
    :param cnt: 每个查询的重复测试次数
    :param workers: 并发工作进程数
    :param base_url: PQL服务基础地址（当type=pql时生效）
    :param window: 时间窗口大小（秒），0表示不分割时间范围

    示例：
    ketacli benchmark_for_file --file queries.txt --type spl --workers 4 --cnt 10
    """
    with open(file_path, "r") as f:
        querys = f.readlines()

    benchmark(type=type, query=querys, start=start, end=end, limit=limit, cnt=cnt, workers=workers, base_url=base_url,
              window=window)


@command
def plot(spl, start=None, end=None, limit=100, interval=3.0,
         type="line", title=None, x_label="Time", y_label="Value", x_field="_time",
         y_field="value", group_field="", extra=None, theme=None, ):
    """plot chart of a single plot.

    :param spl: The spl query
    :param --start: The start time. Time format "2024-01-02 10:10:10"
    :param --end: The start time. Time format "2024-01-02 10:10:10"
    :param -l, --limit: The limit size of query result
    :param --interval: refresh the resource change
    :param -t, --type: plot type, line|bar|scatter
    :param --title: plot title
    :param --x_label: x label
    :param --y_label: y label
    :param -x, --x_field: x field
    :param -y, --y_field: y field
    :param -g, --group_field: group field
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if start is not None:
        start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    if end is not None:
        end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
    if not title:
        title = spl
    extra_args_map = {}
    if extra:
        extra_args_map = parse_url_params(extra)

    config = {
        "layout": {
            "rows": 1,
            "columns": 1
        },
        "charts": [
            {
                "type": type,
                "title": title,
                "x_label": x_label,
                "y_label": y_label,
                "x_field": x_field,
                "y_field": y_field,
                "group_field": group_field,
                "plot_type": type,
                "extra_args": extra_args_map,
                "position": "row0-col0",
                "spl": spl,
                "start": start,
                "end": end,
                "limit": limit,
                "theme": theme,
                "interval": interval
            }
        ]
    }
    chart = LayoutChart(config)
    chart.live(interval=interval, theme=theme)


@command
@arg("chart", type=str, completer=lambda prefix, **kwd: [
    x.replace('.yaml', '').replace('.yml', '')
    for x in os.listdir(resource_filename('ketacli', "charts")) if x.startswith(prefix)
])
@arg("theme", type=str,
     completer=lambda prefix, **kwd: [
         x for x in ["default", "dark", "clear", "pro", "matrix", "windows",
                     "retro", "elegant", "mature", "dreamland", "grandpa",
                     "salad", "girly", "serious", "sahara", 'scream'] if x.startswith(prefix)
     ])
def dashboard(chart=None, file_path=None, interval=30, theme="", disable_auto_refresh=True):
    """plot dashboard from yaml file

    :param -c, --chart: The chart name, such as monitor
    :param -f, --file_path: The file path
    :param --interval: refresh the chart change, default 30s
    :param --theme: setting the theme, such as default|dark|clear|pro|matrix|windows|retro|elegant|mature|dreamland|grandpa|salad|girly|serious|sahara|scream
    :param -d, --disable_auto_refresh: auto refresh the chart change
    """
    if file_path is None and chart is None:
        console.print(f"Please specify file path with --file or --chart")
        return
    if chart is not None:
        file_path = os.path.join(resource_filename('ketacli', "charts"), f"{chart}.yaml")
    config = yaml.safe_load(open(file_path, encoding="utf-8"))
    chart = LayoutChart(config)
    chart.live(interval=interval, theme=theme, disable_auto_refresh=disable_auto_refresh)


@command
def insert(repo="default", data=None, file=None):
    """Upload data to specified repo

    :param --repo: The target repo
    :param --data: The json string data [{"raw":"this is text", "host": "host-1"}]
    :param --file: Upload json text from file path.
    """
    if repo is None:
        console.print(f"Please specify target repo with --repo")
        return
    if data is None and file is None:
        console.print(f"Please use --data or --file to specify data to upload")
        return

    if file is not None:
        f = open(file, encoding="utf-8")
        data = f.read()

    query_params = {
        "repo": repo,
    }
    resp = request_post("data", json.loads(data), query_params).json()
    console.print(resp, overflow="fold")


@command
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def create(asset_type, name=None, data=None, file=None, extra=None):
    """Create asset

    :param asset_type: The target asset type, such as repo, sourcetype ...
    :param -n, --name: The target asset name
    :param --data: The json string data {...}
    :param --file: Upload json text from file path.
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if data is None and file is None:
        content = {}
    else:
        content = data
        if file is not None:
            f = open(file, encoding="utf-8")
            content = f.read()
        try:
            content = json.loads(content)
        except json.JSONDecodeError as e:
            console.print("JSON 解析错误:", e)
            return
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    if 'name' in extra_args_map:
        name = extra_args_map.pop('name')
    req = create_asset_request(asset_type, name, content, **extra_args_map)
    resp = request(req["method"], req["path"], data=req['data']).json()
    console.print(resp, overflow="fold")


def get_operation_type(prefix, **kwargs):
    operators = []
    for x in get_resources():
        if x == kwargs.get('parsed_args').asset_type:
            methods = get_resources()[x].get('methods')
            operators = methods.keys()
    operators = [x for x in operators if
                 x not in ['list', 'create', 'update', 'delete', 'download', 'get'] and x.startswith(prefix)]
    return operators


@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
@command
@arg("operation", type=str, completer=get_operation_type)
def update(asset_type, name=None, operation="update", data=None, file=None, extra=None):
    """Create asset

    :param asset_type: The target asset type, such as repo, sourcetype ...
    :param -n, --name: The target asset name
    :param -d, --data: The json string data {...}
    :param -f, --file: Upload json text from file path.
    :param -o, --operation: operation type, such as open, close, update, delete
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if data is None and file is None:
        data = {}
    else:
        content = data
        if file is not None:
            f = open(file, encoding="utf-8")
            content = f.read()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            console.print("JSON 解析错误:", e)
            return
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    if 'name' in extra_args_map:
        name = extra_args_map.pop('name')
    req = update_asset_request(asset_type, operation, name, data, **extra_args_map)
    resp = request(req["method"], req["path"], data=req['data']).json()
    console.print(resp, overflow="fold")


@command
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def download(asset_type, extra=None, base_path="./"):
    """export file asset

    :param asset_type: The target asset type, such as repo, sourcetype ...
    :param -e, --extra: extra args, example:id=1234567890,name=test
    :param --base_path: the file save path
    """
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}

    req = export_asset_request(asset_type, **extra_args_map)
    download_file(req["path"], save_path=base_path)


@command
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def delete(asset_type, name=None, data=None, file=None, extra=None):
    """Delete asset

    :param --asset_type: The target asset type, such as repo, sourcetype ...
    :param -n, --name: The target asset name or id
    :param -d, --data: The json string data {...}
    :param -f, --file: Upload json text from file path.
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if data is None and file is None:
        data = {}
    else:
        content = data
        if file is not None:
            f = open(file, encoding="utf8")
            content = f.read()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            console.print("JSON 解析错误:", e)
            return

    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    if 'name' in extra_args_map:
        name = extra_args_map.pop('name')

    req = delete_asset_request(asset_type, name, data, **extra_args_map)
    resp = request(req["method"], req["path"], data=req['data']).json()
    console.print(resp, overflow="fold")


@command
@arg('type', type=str, completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def rs(type=None, format="table"):
    """Show resource info

    :param -t, --type: The target asset type, such as repo, sourcetype ...
    :param -f, --format: The output format, text, json ...
    """
    resources = get_resources()
    if type is None:
        table = rs_output_all(resources)
    else:
        table = rs_output_one(type, resources.get(type))
    console.print(format_table(table, format=format), overflow="fold")


@command
@arg('name', '-n', '--name', type=str,
     completer=lambda prefix, **kwd: [x['name'] for x in list_clusters() if x['name'].startswith(prefix)])
@arg('operation', type=str,
     completer=lambda prefix, **kwd: [x for x in ['list-clusters', 'set-default', 'delete-cluster'] if
                                      x.startswith(prefix)])
def config(operation, name=None):
    """Show keta cluster info

    :param operation: The target operation, such as list-clusters, set-default, delete-cluster
    :param -n, --name: setting or delete default cluster
    """
    resp = []
    if operation not in ["list-clusters", "set-default", "delete-cluster"]:
        console.print(f"Please specify operation, such as list-clusters, set-default, delete-cluster", style="red")
        return
    if operation == "list-clusters":
        resp = list_clusters()
    elif operation == "set-default":
        resp = set_default_cluster(name)
    elif operation == "delete-cluster":
        resp = delete_cluster(name)
    if not resp:
        console.print("No response")
        exit()
    table = list_output('cluster', [], resp=resp)
    console.print(format_table(table, "table"), overflow="fold")


@command
def version():
    _version = importlib.metadata.version('ketacli')
    console.print(_version, overflow="fold")


@command
@arg('overflow', '-o', '--overflow', type=str,
     completer=lambda prefix, **kwd: [x for x in ["fold", "crop", "ellipsis", "ignore"] if x.startswith(prefix)])
def isearch(page_size=10, limit=500, overflow="ellipsis"):
    """
    interactive search, 该模式仅支持在界面化系统中允许，无法通过 ssh 连接到服务器来运行

    :params --page_size: page size, default 10
    :params --limit: search data number, default 500
    :params --overflow: 文本超出列宽度时的处理方式, default ellipsis ，可选 ["fold", "crop", "ellipsis", "ignore"]

    """
    try:
        from ketacli.sdk.chart.interactive_search import InteractiveSearch
        InteractiveSearch(page_size=page_size, limit=limit, overflow=overflow).loop()
    except Exception as e:
        console.print_exception()


def start():
    # 确保main被正确初始化
    import argcomplete
    argcomplete.autocomplete(main.parser)
    try:
        argcomplete.autocomplete(main.parser)
        main()
    except Exception:
        console.print_exception()


if __name__ == "__main__":
    start()
