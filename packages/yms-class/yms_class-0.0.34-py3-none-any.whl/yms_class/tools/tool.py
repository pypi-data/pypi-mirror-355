import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List

import click
import numpy as np
import pandas as pd
import pytz
import torch
import wandb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, \
    classification_report
from tqdm import tqdm


# 读取txt内两个不同表格的数据，并将结果转换为字典列表输出
def read_multi_table_txt(file_path):
    # 读取原始内容
    with open(file_path, 'r') as f:
        content = f.read()

    # 按表格标题分割内容（假设每个新表格以"epoch"开头）
    table_blocks = re.split(r'\n(?=epoch\s)', content.strip())

    # 处理每个表格块
    table_dicts = []
    for block in table_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]

        # 解析列名（处理制表符和混合空格）
        columns = re.split(r'\s{2,}|\t', lines[0])

        # 解析数据行（处理混合分隔符）
        data = []
        for line in lines[1:]:
            # 使用正则表达式分割多个连续空格/制表符
            row = re.split(r'\s{2,}|\t', line)
            data.append(row)

        # 创建DataFrame并自动转换数值类型
        df = pd.DataFrame(data, columns=columns)
        df = df.apply(pd.to_numeric, errors='coerce')  # 自动识别数值列，非数值转换为NaN

        # 将DataFrame转换为字典，每列以列表形式保存
        table_dict = df.to_dict(orient='list')
        table_dicts.append(table_dict)

    return table_dicts


def get_current_time(format_str="%Y-%m-%d %H:%M:%S"):
    """
    获取东八区（UTC+8）的当前时间，并返回指定格式的字符串
    :param format_str: 时间格式（默认为 "%Y-%m-%d %H:%M:%S"）
    :return: 格式化后的时间字符串
    """

    # 创建东八区的时区对象
    utc8_timezone = timezone(timedelta(hours=8))

    # 转换为东八区时间
    utc8_time = datetime.now(utc8_timezone)

    # 格式化为字符串
    formatted_time = utc8_time.strftime(format_str)
    return formatted_time


# val和test时的相关结果指标计算
def calculate_results(all_labels, all_predictions, classes, average='macro'):
    results = {
        'accuracy': accuracy_score(y_true=all_labels, y_pred=all_predictions),
        'precision': precision_score(y_true=all_labels, y_pred=all_predictions, average=average),
        'recall': recall_score(y_true=all_labels, y_pred=all_predictions, average=average),
        'f1_score': f1_score(y_true=all_labels, y_pred=all_predictions, average=average),
        'cm': confusion_matrix(y_true=all_labels, y_pred=all_predictions, labels=np.arange(len(classes)))
    }
    return results


def calculate_metric(all_labels, all_predictions, classes, class_metric=False, average='macro avg'):
    metric = classification_report(y_true=all_labels, y_pred=all_predictions,
                                   target_names=classes, digits=4, output_dict=True, zero_division=0)
    if not class_metric:
        metric = {
            'accuracy': metric.get('accuracy'),
            'precision': metric.get(average).get('precision'),
            'recall': metric.get(average).get('recall'),
            'f1-score': metric.get(average).get('f1-score'),
        }
        return metric
    else:
        return metric


def initialize_results_file(results_file, result_info):
    """
    初始化结果文件，确保文件存在且第一行包含指定的内容。

    参数:
        results_file (str): 结果文件的路径。
        result_info (list): 需要写入的第一行内容列表。
    """
    # 处理 result_info，在每个单词后添加两个空格
    result_info_str = '  '.join(result_info) + '\n'
    # 检查文件是否存在
    if os.path.exists(results_file):
        # 如果文件存在，读取第一行
        with open(results_file, "r") as f:
            first_line = f.readline().strip()
        # 检查第一行是否与 result_info 一致
        if first_line == result_info_str.strip():
            print(f"文件 {results_file} 已存在且第一行已包含 result_info，不进行写入。")
        else:
            # 如果不一致，写入 result_info
            with open(results_file, "w") as f:
                f.write(result_info_str)
            print(f"文件 {results_file} 已被重新初始化。")
    else:
        # 如果文件不存在，创建并写入 result_info
        with open(results_file, "w") as f:
            f.write(result_info_str)
        print(f"文件 {results_file} 已创建并写入 result_info。")


def is_similar_key(key1, key2):
    """
    检查两个键是否相似，考虑复数形式的转换。

    Args:
        key1 (str): 第一个键
        key2 (str): 第二个键

    Returns:
        bool: 如果两个键相似（包括复数形式的转换），返回 True，否则返回 False
    """
    if key1 == key2:
        return True

    # 检查 key2 是否是复数形式
    if key2.endswith("ies"):
        singular_candidate = key2.removesuffix("ies") + "y"
        if key1 == singular_candidate:
            return True

    if key2.endswith("es"):
        singular_candidate = key2.removesuffix("es")
        if key1 == singular_candidate:
            return True

    if key2.endswith("s"):
        singular_candidate = key2.removesuffix("s")
        if key1 == singular_candidate:
            return True

    return False


def append_to_results_file(file_path: str,
                           data_dict: dict,
                           column_order: list,
                           float_precision: int = 4,
                           more_float: int = 2,
                           custom_column_widths: dict = None) -> None:
    """
    通用格式化文本行写入函数

    参数：
    file_path: 目标文件路径
    data_dict: 包含数据的字典，键为列名
    column_order: 列顺序列表，元素为字典键
    float_precision: 浮点数精度位数 (默认5位)
    more_float: 额外的浮点数精度位数
    custom_column_widths: 自定义列宽的字典，键为列名，值为列宽
    """
    # 计算每列的最大宽度
    column_widths = []
    formatted_data = []
    for col in column_order:
        # 查找 data_dict 中相似的键
        dict_key = None
        for key in data_dict:
            if is_similar_key(key, col):
                dict_key = key
                break
        if dict_key is None:
            raise ValueError(f"Missing required column: {col}")

        value = data_dict[dict_key]

        # 根据数据类型进行格式化
        if isinstance(value, (int, np.integer)):
            fmt_value = f"{value:d}"
        elif isinstance(value, (float, np.floating)):
            if col in ['train_losses', 'val_losses']:  # 如果列名是'train_losses'或'val_losses'，保留浮点数精度位数+1位
                fmt_value = f"{value:.{float_precision + more_float}f}"
            elif col == 'lrs':
                fmt_value = f"{value:.8f}"
            else:
                fmt_value = f"{value:.{float_precision}f}"
        elif isinstance(value, str):
            fmt_value = value
        else:  # 处理其他类型转换为字符串
            fmt_value = str(value)

        # 确定列宽
        if custom_column_widths and col in custom_column_widths:
            column_width = custom_column_widths[col]
        else:
            # 取列名长度和数值长度的最大值作为列宽
            column_width = max(len(col), len(fmt_value))
        column_widths.append(column_width)

        # 应用列宽对齐
        if col == column_order[-1]:  # 最后一列左边对齐
            fmt_value = fmt_value.ljust(column_width)
        else:
            fmt_value = fmt_value.rjust(column_width)

        formatted_data.append(fmt_value)

    # 构建文本行并写入，列之间用两个空格分隔
    line = "  ".join(formatted_data) + '\n'
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(line)


def make_save_dirs(root_dir):
    img_dir = os.path.join(root_dir, 'images')
    model_dir = os.path.join(root_dir, 'models')
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    print(f'The output folder:{img_dir},{model_dir} has been created.')
    return img_dir, model_dir


def list_folders(path):
    # 获取目录下的所有内容
    entries = os.listdir(path)
    # 筛选只保留文件夹
    folders = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]
    return folders


def get_wandb_key(key_path):
    with open(key_path, 'r', encoding='utf-8') as f:
        key = f.read()
    return key


def wandb_init(project=None, key_path=None, name=None):
    run = None
    if project is not None:
        if key_path is None:
            raise ValueError("When 'project' is not None, 'key_path' should also not be None.")
        wandb_key = get_wandb_key(key_path)
        wandb.login(key=wandb_key)
        run = wandb.init(project=project, name=name)
    return run


def check_wandb_login_required():
    """兼容旧版的登录检查函数"""
    # 优先检查环境变量
    if os.environ.get("WANDB_API_KEY"):
        return False

    try:
        api = wandb.Api()
        # 方法 1：通过 settings 检查（适用于旧版）
        if hasattr(api, "settings") and api.settings.get("entity"):
            return False

        # 方法 2：通过 projects() 验证（通用性强）
        api.projects(per_page=1)  # 仅请求第一页的第一个项目
        return False
    except Exception as e:
        print(f"检测到意外错误: {str(e)}")
        return True  # 保守返回需要登录


def get_wandb_runs(
        project_path: str,
        default_name: str = "未命名",
        api_key: Optional[str] = None,
        per_page: int = 1000
) -> List[Dict[str, str]]:
    """
    获取指定 WandB 项目的所有运行信息（ID 和 Name）

    Args:
        project_path (str): 项目路径，格式为 "username/project_name"
        default_name (str): 当运行未命名时的默认显示名称（默认："未命名"）
        api_key (str, optional): WandB API 密钥，若未设置环境变量则需传入
        per_page (int): 分页查询每页数量（默认1000，用于处理大量运行）

    Returns:
        List[Dict]: 包含运行信息的字典列表，格式 [{"id": "...", "name": "..."}]

    Raises:
        ValueError: 项目路径格式错误
        wandb.errors.UsageError: API 密钥无效或未登录
    """
    # 参数校验
    if "/" not in project_path or len(project_path.split("/")) != 2:
        raise ValueError("项目路径格式应为 'username/project_name'")

    # 登录（仅在需要时）
    if api_key:
        wandb.login(key=api_key)
    elif not wandb.api.api_key:
        raise wandb.errors.UsageError("需要提供API密钥或预先调用wandb.login()")

    # 初始化API
    api = wandb.Api()

    try:
        # 分页获取所有运行（自动处理分页逻辑）
        runs = api.runs(project_path, per_page=per_page)
        print(f'共获取{len(runs)}个run')
        result = [
            {
                "id": run.id,
                "name": run.name or default_name,
                "url": run.url,  # 增加实用字段
                "state": run.state,  # 包含运行状态
                "time": run.metadata['startedAt']
            }
            for run in runs
        ]
        beijing_tz = pytz.timezone('Asia/Shanghai')
        for res in result:
            res["time"] = (
                datetime.strptime(res["time"], "%Y-%m-%dT%H:%M:%S.%fZ")
                .replace(tzinfo=pytz.utc)
                .astimezone(beijing_tz)
                .strftime("%Y-%m-%d %H:%M:%S.%f")
            )
        result.sort(key=lambda x: x["time"], reverse=True)
        return result

    except wandb.errors.CommError as e:
        raise ConnectionError(f"连接失败: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"获取运行数据失败: {str(e)}") from e


def delete_runs(
        project_path: str,
        run_ids: Optional[List[str]] = None,
        run_names: Optional[List[str]] = None,
        delete_all: bool = False,
        dry_run: bool = True,
        api_key: Optional[str] = None,
        per_page: int = 500
) -> dict:
    """
    多功能WandB运行删除工具

    :param project_path: 项目路径（格式：username/project_name）
    :param run_ids: 指定要删除的运行ID列表（无视状态）
    :param run_names: 指定要删除的运行名称列表（无视状态）
    # :param preserve_states: 保护状态列表（默认保护 finished/running）
    :param delete_all: 危险模式！删除所有运行（默认False）
    :param dry_run: 模拟运行模式（默认True）
    :param api_key: WandB API密钥
    :param per_page: 分页查询数量
    :return: 操作统计字典

    使用场景：
    1. 删除指定运行：delete_runs(..., run_ids=["abc","def"])
    2. 默认删除失败运行：delete_runs(...)
    3. 删除所有运行：delete_runs(..., delete_all=True)
    """
    preserve_states: List[str] = ["finished", "running"]
    # 参数校验
    if not project_path.count("/") == 1:
        raise ValueError("项目路径格式应为 username/project_name")
    if delete_all and (run_ids or run_names):
        raise ValueError("delete_all模式不能与其他筛选参数同时使用")

    # 身份验证
    if api_key:
        wandb.login(key=api_key)
    elif not wandb.api.api_key:
        raise wandb.errors.UsageError("需要API密钥或预先登录")

    api = wandb.Api()
    stats = {
        "total": 0,
        "candidates": 0,
        "deleted": 0,
        "failed": 0,
        "dry_run": dry_run
    }

    try:
        runs = api.runs(project_path, per_page=per_page)
        stats["total"] = len(runs)

        # 确定删除目标
        if delete_all:
            targets = runs
            click.secho("\n⚠️ 危险操作：将删除项目所有运行！", fg="red", bold=True)
        elif run_ids or run_names:
            targets = [
                run for run in runs
                if run.id in (run_ids or []) or run.name in (run_names or [])
            ]
            print(f"\n找到 {len(targets)} 个指定运行")
        else:
            targets = [run for run in runs if run.state not in preserve_states]
            print(f"\n找到 {len(targets)} 个非正常状态运行")

        stats["candidates"] = len(targets)

        if not targets:
            print("没有符合条件的运行")
            return stats

        # 打印预览
        print("\n待删除运行示例：")
        for run in targets[:3]:
            state = click.style(run.state, fg="green" if run.state == "finished" else "red")
            print(f" • {run.id} | {run.name} | 状态：{state}")
        if len(targets) > 3:
            print(f" ...（共 {len(targets)} 条）")

        # 安全确认
        if dry_run:
            click.secho("\n模拟运行模式：不会实际删除", fg="yellow")
            return stats

        if delete_all:
            msg = click.style("确认要删除所有运行吗？此操作不可逆！", fg="red", bold=True)
        else:
            msg = f"确认要删除 {len(targets)} 个运行吗？"

        if not click.confirm(msg, default=False):
            print("操作已取消")
            return stats

        # 执行删除
        print("\n删除进度：")
        for i, run in enumerate(targets, 1):
            try:
                run.delete()
                stats["deleted"] += 1
                print(click.style(f"  [{i}/{len(targets)}] 已删除 {run.id}", fg="green"))
            except Exception as e:
                stats["failed"] += 1
                print(click.style(f"  [{i}/{len(targets)}] 删除失败 {run.id}: {str(e)}", fg="red"))

        return stats

    except wandb.errors.CommError as e:
        raise ConnectionError(f"网络错误: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"操作失败: {str(e)}")


def get_all_artifacts_from_project(project_path, max_runs=None, run_id=None):
    """获取WandB项目或指定Run的所有Artifact

    Args:
        project_path (str): 项目路径，格式为 "entity/project"
        max_runs (int, optional): 最大获取Run数量（仅当未指定run_id时生效）
        run_id (str, optional): 指定要查询的Run ID

    Returns:
        list: 包含所有Artifact对象的列表
    """
    api = wandb.Api()
    all_artifacts = []
    seen_artifacts = set()  # 用于去重

    try:
        if run_id:
            # 处理单个Run的情况
            run = api.run(f"{project_path}/{run_id}")
            artifacts = run.logged_artifacts()

            for artifact in artifacts:
                artifact_id = f"{artifact.name}:{artifact.version}"
                if artifact_id not in seen_artifacts:
                    all_artifacts.append(artifact)
                    seen_artifacts.add(artifact_id)

            print(f"Found {len(all_artifacts)} artifacts in run {run_id}")
        else:
            # 处理整个项目的情况
            runs = api.runs(project_path, per_page=500)
            run_iterator = tqdm(runs[:max_runs] if max_runs else runs,
                                desc=f"Scanning {project_path}")

            for run in run_iterator:
                try:
                    artifacts = run.logged_artifacts()
                    for artifact in artifacts:
                        artifact_id = f"{artifact.name}:{artifact.version}"
                        if artifact_id not in seen_artifacts:
                            all_artifacts.append(artifact)
                            seen_artifacts.add(artifact_id)
                except Exception as run_error:
                    print(f"Error processing run {run.id}: {str(run_error)}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

    return all_artifacts

def get_id(target_name, res):
    df = pd.DataFrame.from_records(res)
    # 筛选状态既不是 'finished' 也不是 'running' 的记录
    filtered = df[(df['name'] == target_name) & ~df['state'].isin(['finished', 'running'])]['id']

    if not filtered.empty:
        # 存在符合条件的记录，返回第一个 id
        return filtered.iloc[0]
    else:
        # 无符合条件的记录，获取该 name 最新的 id（按 id 降序排列取第一个）
        name_df = df[df['name'] == target_name]
        if name_df.empty:
            return '001'  # 无该 name 的任何记录时返回 None
        latest_id_str = name_df['id'].iloc[0]
        # 转为数值加 1 后再格式化为三位字符串
        new_id_num = int(latest_id_str) + 1
        return f"{new_id_num:03d}"


def count_model_params(model: torch.nn.Module,
                       verbose: bool = False,
                       only_trainable: bool = False) -> dict:
    """
    统计PyTorch模型参数量（支持参数分类）

    参数:
        model: 目标模型
        verbose: 是否打印详细信息
        only_trainable: 是否仅统计可训练参数

    返回:
        参数字典 {
            'total': 总参数数量,
            'trainable': 可训练参数数量（仅当only_trainable=False时有效）,
            'non_trainable': 非可训练参数数量（仅当only_trainable=False时有效）
        }
    """
    param_dict = {'total': 0, 'trainable': 0, 'non_trainable': 0}

    for name, param in model.named_parameters(recurse=True):
        # 跳过缓冲区（如BN的running_mean/var）
        if isinstance(param, torch.nn.Parameter):
            num = param.numel()
            param_dict['total'] += num
            if param.requires_grad:
                param_dict['trainable'] += num
            else:
                param_dict['non_trainable'] += num

    if only_trainable:
        param_dict = {'trainable': param_dict['trainable']}

    # 可读性格式化
    def format_num(x):
        return f"{x:,}" if x > 1e4 else f"{x}"

    if verbose:
        print(f"{'参数类型':<15} 数量 ({'可训练' if only_trainable else '总计'})")
        print("-" * 40)
        if only_trainable:
            print(f"{'可训练参数':<15} {format_num(param_dict['trainable'])}")
        else:
            print(f"{'总参数':<15} {format_num(param_dict['total'])}")
            print(f"  ├─ 可训练参数: {format_num(param_dict['trainable'])}")
            print(f"  └─ 非可训练参数: {format_num(param_dict['non_trainable'])}")
        print(f"\n设备: {next(model.parameters()).device.type if model.parameters() else 'cpu'}")

    return param_dict

