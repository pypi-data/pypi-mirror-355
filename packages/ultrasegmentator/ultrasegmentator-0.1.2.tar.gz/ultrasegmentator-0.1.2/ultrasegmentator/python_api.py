import sys
import os
import zipfile

import numpy as np
import urllib
import torch
import re

from pathlib import Path
from typing import Union
from ultrasegmentator.paths import nnUNet_results, nnUNet_raw
from ultrasegmentator.inference.predict_from_raw_data import *


def validate_device_type_api(value):
    valid_strings = ["gpu", "cpu", "mps"]
    if value in valid_strings:
        return value

    # Check if the value matches the pattern "gpu:X" where X is an integer
    pattern = r"^gpu:(\d+)$"
    match = re.match(pattern, value)
    if match:
        device_id = int(match.group(1))
        return value

    raise ValueError(
        f"Invalid device type: '{value}'. Must be 'gpu', 'cpu', 'mps', or 'gpu:X' where X is an integer representing the GPU device ID.")


def convert_device_to_cuda(device):
    if device in ["cpu", "mps", "gpu"]:
        return device
    else:  # gpu:X
        return f"cuda:{device.split(':')[1]}"


def get_cache_dir() -> Path:
    """
    获取系统缓存目录路径（跨平台）
    Windows: %LOCALAPPDATA%\\Temp
    Linux: /var/tmp 或 /tmp
    """
    if sys.platform.startswith('win'):
        # Windows 缓存路径
        cache_base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return Path(cache_base) / 'Temp'
    else:
        # Linux/Unix 缓存路径
        for path in ('/var/tmp', '/tmp'):
            if os.path.isdir(path):
                return Path(path)
        # 回退到用户目录
        return Path.home() / '.cache'


def download_and_unzip_parts(url: list, output_dir: str) -> str:
    """
    下载分块文件并解压
    :param url: 分块文件的 URL 列表
    :param file_path: 目标文件路径
    :param output_dir: 解压输出目录
    :return: 解压输出目录的路径
    """
    # 检查输出目录是否存在,是否为空
    if os.path.exists(output_dir) and os.listdir(output_dir):
        print(f"目标目录 {output_dir} 已存在，跳过下载和解压。")
        output_dir = os.path.join(output_dir, os.listdir(output_dir)[0])
        return output_dir
    # 创建目标目录
    file_path = os.path.join(output_dir, "downloaded_file.zip")
    os.makedirs(output_dir, exist_ok=True)

    # 获取分块文件的数量
    num_parts = len(url)

    # 下载并保存每个分块文件
    for i in range(num_parts):
        print(f"开始下载分块文件 {i + 1}/{num_parts}: {url[i]}")
        try:
            # 下载文件
            urllib.request.urlretrieve(url[i], file_path + f".part{i + 1}")
            print(f"分块文件 {i + 1} 已保存到: {file_path}.part{i + 1}")
        except Exception as e:
            # 清理已下载的分块文件
            for j in range(i + 1):
                if os.path.exists(file_path + f".part{j + 1}"):
                    os.remove(file_path + f".part{j + 1}")
            raise RuntimeError(f"下载分块文件 {i + 1} 失败: {e}") from e

    # 合并分块文件
    print("开始合并分块文件...")
    with open(file_path, "wb") as f_out:
        for i in range(num_parts):
            with open(file_path + f".part{i + 1}", "rb") as f_in:
                f_out.write(f_in.read())
            # 删除已合并的分块文件
            os.remove(file_path + f".part{i + 1}")
    print("文件合并完成!")

    # 解压文件
    print(f"开始解压文件: {file_path}")
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
        print(f"文件已解压到: {output_dir}")
    except Exception as e:
        # 清理已合并的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise RuntimeError(f"解压文件失败: {e}") from e

    # 删除已解压的文件
    if os.path.exists(file_path):
        os.remove(file_path)

    # output_dir添加下一级文件夹
    output_dir = os.path.join(output_dir, os.listdir(output_dir)[0])

    return output_dir


# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partaa
# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partab
# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partac
# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partad

# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partaa
# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partab
# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partac
# https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partad


def pred(input: Union[str, Path], output: Union[str, Path, None] = None, task: str = "CAMUS_Left_Heart", device: str = "cuda"):
    """
    Ultrasegmentator API for nnUNet inference.
    :param input:
    :param output:
    :param task: str, one of the following:"CAMUS_Left_Heart", "Four_Chamber_Heart"
    :return:
    """
    tile_step_size = 0.5
    use_gaussian = True
    use_mirroring = True
    perform_everything_on_device = True
    verbose = False
    quiet = False
    save_probabilities = False
    skip_saving = False
    force_split = False
    nr_thr_resamp = 1
    nr_thr_saving = 6
    num_parts = 1
    part_id = 0

    # 处理设备参数
    device = torch.device('cuda') if device == "gpu" else torch.device('cpu')

    # 初始化预测器
    predictor = nnUNetPredictor(
        tile_step_size=tile_step_size,
        use_gaussian=use_gaussian,
        use_mirroring=use_mirroring,
        perform_everything_on_device=perform_everything_on_device,
        device=device,
        verbose=verbose,  # 使用用户指定的verbose参数
        verbose_preprocessing=verbose,
        allow_tqdm=not quiet  # quiet模式关闭tqdm进度条
    )

    cache_dir = get_cache_dir()
    if task == "CAMUS_Left_Heart":
        url_list = [
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partaa',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partab',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partac',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset509_CAMUS_Left_Heart.partad'
        ]
        cache_dir = os.path.join(cache_dir, "CAMUS_Left_Heart")
        cache_dir  = download_and_unzip_parts(url_list, cache_dir)
    elif task == "Four_Chamber_Heart":
        url_list = [
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partaa',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partab',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partac',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_2/releases/download/v1.0.0/Dataset510_Four_Chamber_Heart.partad'
        ]
        cache_dir = os.path.join(cache_dir, "Four_Chamber_Heart")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    else:
        raise ValueError(f"Unsupported task: {task}. Supported tasks are: CAMUS_Left_Heart, Four_Chamber_Heart.")

    # 处理输出路径
    if skip_saving:
        output = None
    else:
        if output is None and not os.path.exists(output):
            output.mkdir(parents=True, exist_ok=True)

    # 加载预训练模型
    predictor.initialize_from_path(str(cache_dir))

    # 核心预测调用
    predictor.predict_from_files(
        str(input),
        str(output) if output else None,
        save_probabilities=save_probabilities,
        overwrite=force_split,  # 映射force_split到覆盖选项
        num_processes_preprocessing=nr_thr_resamp,
        num_processes_segmentation_export=nr_thr_saving,
        folder_with_segs_from_prev_stage=None,
        num_parts=num_parts,
        part_id=part_id
    )
