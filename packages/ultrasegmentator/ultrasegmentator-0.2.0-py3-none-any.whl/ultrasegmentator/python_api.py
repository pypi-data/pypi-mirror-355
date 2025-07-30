import sys
import os
import zipfile
import argparse 

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
    if device in ["cpu", "mps"]:
        return device
    elif device == 'gpu':
        return 'cuda'
    else:  # gpu:X
        return f"cuda:{device.split(':')[1]}"


def get_cache_dir() -> Path:
    """
    Get the system cache directory path (cross-platform)
    Windows: %LOCALAPPDATA%\\Temp
    Linux: /var/tmp or /tmp
    """
    if sys.platform.startswith('win'):
        # Windows cache path
        cache_base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return Path(cache_base) / 'Temp'
    else:
        # Linux/Unix cache path
        for path in ('/var/tmp', '/tmp'):
            if os.path.isdir(path):
                return Path(path)
        # Fallback to user directory
        return Path.home() / '.cache'


def download_and_unzip_parts(url: list, output_dir: str) -> str:
    """
    Download split files and unzip them
    :param url: List of URLs for split files
    :param output_dir: Unzip output directory
    :return: Path to the unzipped output directory
    """
    # Check if the output directory exists and is not empty
    if os.path.exists(output_dir) and os.listdir(output_dir):
        print(f"Target directory {output_dir} already exists, skipping download and unzip.")
        output_dir = os.path.join(output_dir, os.listdir(output_dir)[0])
        return output_dir
    # Create target directory / 创建目标目录
    file_path = os.path.join(output_dir, "downloaded_file.zip")
    os.makedirs(output_dir, exist_ok=True)

    # Get the number of split files
    num_parts = len(url)

    # Download and save each split file 
    for i in range(num_parts):
        print(f"Starting to download split file {i + 1}/{num_parts}: {url[i]}")
        try:
            # Download file / 下载文件
            urllib.request.urlretrieve(url[i], file_path + f".part{i + 1}")
            print(f"Split file {i + 1} saved to: {file_path}.part{i + 1}")
        except Exception as e:
            # Clean up downloaded split files
            for j in range(i + 1):
                if os.path.exists(file_path + f".part{j + 1}"):
                    os.remove(file_path + f".part{j + 1}")
            raise RuntimeError(f"Failed to download split file {i + 1}: {e}") from e

    # Merge split files
    print("Starting to merge split files...")
    with open(file_path, "wb") as f_out:
        for i in range(num_parts):
            with open(file_path + f".part{i + 1}", "rb") as f_in:
                f_out.write(f_in.read())
            # Delete merged split files
            os.remove(file_path + f".part{i + 1}")
    print("File merging completed!")

    # Unzip file 
    print(f"Starting to unzip file: {file_path}")
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
        print(f"File unzipped to: {output_dir}")
    except Exception as e:
        # Clean up merged file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise RuntimeError(f"Failed to unzip file: {e}") from e

    # Delete unzipped file 
    if os.path.exists(file_path):
        os.remove(file_path)

    # Add the next level folder to output_dir
    output_dir = os.path.join(output_dir, os.listdir(output_dir)[0]) 

    return output_dir


def pred(input: Union[str, Path], output: Union[str, Path], task: str , device: str = "gpu"):
    """
    Ultrasegmentator API for nnUNet inference.
    :param input: Input file/directory path (must be a valid existing path)
    :param output: Output directory path (required if saving results). Defaults to None
    :param task: Task name, must be one of: "CAMUS_Left_Heart", "Four_Chamber_Heart", "Carotid_Artery", "Thyroid_Nodule", "Thyroid_Gland", "Fetal_Head", "Fetal_Abdomen", "Breast_Nodule". Defaults to "CAMUS_Left_Heart"
    :param device: Device to use for inference (e.g., "cuda", "cpu"). Defaults to "cuda"
    :return: None
    """
    # Parameter validation
    if not (isinstance(input, (str, Path)) and (os.path.exists(input))):
        raise ValueError(f"Invalid input path: {input}. Must be an existing file or directory.")
    
    if not task or not isinstance(task, str):
        raise ValueError(f"Invalid task: {task}. Must be a non-empty string.")
    
    if output is None:
        raise ValueError("Output path is required when saving results.")

    tile_step_size = 0.5
    use_gaussian = True
    use_mirroring = True
    perform_everything_on_device = True
    verbose = False
    quiet = False
    save_probabilities = False
    skip_saving = False
    overwrite = True
    nr_thr_resamp = 1
    nr_thr_saving = 6
    num_parts = 1
    part_id = 0

    if validate_device_type_api(device):
        device = torch.device(convert_device_to_cuda(device))
    
    
    # device = torch.device(device) if 'cuda' in device else torch.device('cpu')

    # Initialize
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
    elif task == "Carotid_Artery":
        url_list = [
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset505_Carotid_Artery.partaa',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset505_Carotid_Artery.partab',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset505_Carotid_Artery.partac',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset505_Carotid_Artery.partad'
        ]
        cache_dir = os.path.join(cache_dir, "Carotid_Artery")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    elif task == "Thyroid_Nodule":
        url_list = [
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset506_Thyroid_Nodule.partaa',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset506_Thyroid_Nodule.partab',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset506_Thyroid_Nodule.partac'
        ]
        cache_dir = os.path.join(cache_dir, "Thyroid_Nodule")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    elif task == "Thyroid_Gland":
        url_list = [
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset507_Thyroid_Gland.partaa',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset507_Thyroid_Gland.partab',
        ]
        cache_dir = os.path.join(cache_dir, "Thyroid_Gland")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    elif task == "Fetal_Head":
        url_list = [
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset508_Fetal_Head.partaa',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset508_Fetal_Head.partab',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset508_Fetal_Head.partac',
            'https://gitee.com/jacksonyu123_admin/ultrasound_tool_1/releases/download/v1.0.0/Dataset508_Fetal_Head.partad'
        ]
        cache_dir = os.path.join(cache_dir, "Fetal_Head")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    elif task == 'Fetal_Abdomen':
        url_list = [
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset503_FASS.partaa',
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset503_FASS.partab',
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset503_FASS.partac',
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset503_FASS.partad'
        ]
        cache_dir = os.path.join(cache_dir, "Fetal_Abdomen")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    elif task == 'Breast_Nodule':
        url_list = [
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset504_Breast_Nodule.partaa',
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset504_Breast_Nodule.partab',
            'https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Dataset504_Breast_Nodule.partac'
        ]
        cache_dir = os.path.join(cache_dir, "Breast_Nodule")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
    
    else:
        raise ValueError(f"Unsupported task: {task}. Supported tasks are: CAMUS_Left_Heart, Four_Chamber_Heart, Carotid_Artery\
                        Thyroid_Nodule, Thyroid_Gland, Fetal_Head, Fetal_Abdomen, Breast_Nodule.")

    if skip_saving:
        output = None
    else:
        if output is None and not os.path.exists(output):
            output.mkdir(parents=True, exist_ok=True)

    # load pretrained weight
    predictor.initialize_from_path(str(cache_dir))

    # predict
    predictor.predict_from_files(
        str(input),
        str(output) if output else None,
        save_probabilities=save_probabilities,
        overwrite=overwrite, 
        num_processes_preprocessing=nr_thr_resamp,
        num_processes_segmentation_export=nr_thr_saving,
        folder_with_segs_from_prev_stage=None,
        num_parts=num_parts,
        part_id=part_id
    )
    
def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="Ultrasegmentator: Medical Ultrasound image segmentation tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # 必选参数
    parser.add_argument("-i", "--input", required=True, 
                        help="Input file/directory path (must be a valid existing path)")
    parser.add_argument("-o", "--output", required=True, 
                        help="Output directory path (required for saving results)")
    # 可选参数
    parser.add_argument("-t", "--task",  required=True,
                        help=f"Segmentation task name. Supported: CAMUS_Left_Heart, Four_Chamber_Heart, Carotid_Artery, \
                        Thyroid_Nodule, Thyroid_Gland, Fetal_Head, Fetal_Abdomen, Breast_Nodule")
    parser.add_argument("-d", "--device", default="cuda",
                        help="Computation device. Options: 'gpu', 'cpu', 'mps' or 'gpu:X' (X is GPU ID)")
    
    args = parser.parse_args()
    
    # 调用核心预测函数
    pred(
        input=args.input,
        output=args.output,
        task=args.task,
        device=args.device
    )

if __name__ == "__main__":
    main()
