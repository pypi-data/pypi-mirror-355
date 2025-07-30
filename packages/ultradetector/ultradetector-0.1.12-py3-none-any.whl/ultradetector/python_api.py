import shutil
import sys
import os
import numpy as np

import urllib
import torch
import re
import cv2
import datetime
import json
from pathlib import Path
from typing import Union
from ultradetector.ultralytics import YOLO


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


def download_file(url: str, file_path) -> Path:
    """
    下载文件到缓存目录（如果不存在）
    返回下载文件的完整路径
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 检查文件是否已存在
    if os.path.exists(file_path):
        print(f"文件已存在，跳过下载: {file_path}")
        return file_path

    print(f"开始下载: {url}")
    try:
        # 下载文件
        urllib.request.urlretrieve(url, file_path)
        print(f"文件已保存到: {file_path}")
        return file_path
    except Exception as e:
        # 清理可能创建的空文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise RuntimeError(f"下载失败: {e}") from e


def yolo11_detect_predict(input_path, output_path, model_weight, conf, iou):
    # Remove folder if it exists
    if os.path.exists(os.path.join(output_path, f'results/')):
        shutil.rmtree(os.path.join(output_path, f'results/'))

    model = YOLO(model_weight)

    project = os.path.join(output_path, 'results/')
    name = "yoloobb"
    print(f"Strat predict {name}")

    result = model.predict(source=input_path,
                           save_txt=True,
                           save=True,
                           exist_ok=True,
                           #    imgsz=640,
                           conf=conf,
                           iou=iou,
                           project=project,
                           name=name)

    print("Finished!!!")


def pred(input: Union[str, Path], output: Union[str, Path, None] = None, task: str = "Breast_Nudule", device: str = "gpu") -> None:
    """
    Ultrasegmentator API for nnUNet inference.
    :param input:
    :param output:
    :param task: str, one of the following: "Breast_Nudule", "carotid_artery", "Fetal_Abdomen", "Fetal_Head", "Fetal_NT", "Thyroid_Gland", "Thyroid_Nudule"
    :param device: "gpu" or "cpu" or "mps" or "gpu:X" where X is the GPU device ID
    :return:
    """
    # 处理设备参数
    device = torch.device('cuda') if device == "gpu" else torch.device('cpu')

    cache_dir = get_cache_dir()
    # 检查模型路径是否存在，如果不存在则下载
    if task == "CAMUS_Left_Heart":
        model_url = "https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.1/CAMUS_Left_Heart_yolov11-m_384%C3%97384_best.pt"
        download_file(model_url, os.path.join(cache_dir, "CAMUS_Left_Heart_yolov11-m_384x384_best.pt"))
        pth_path = os.path.join(cache_dir, "CAMUS_Left_Heart_yolov11-m_384x384_best.pt")
    elif task == "Breast_Nudule":
        model_url = "https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Breast_Nodule_yolov11-m_640%C3%97640_best.pt"  # 替换为实际的模型下载链接
        download_file(model_url, os.path.join(cache_dir, "Breast_Nudule_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Breast_Nudule_yolov11-m_640x640_best.pt")
    elif task == "carotid_artery":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/carotid_artery_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "carotid_artery_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "carotid_artery_yolov11-m_640x640_best.pt")
    elif task == "Fetal_Abdomen":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Fetal_Abdomen_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Fetal_Abdomen_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Fetal_Abdomen_yolov11-m_640x640_best.pt")
    elif task == "Fetal_Head":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Fetal_Head_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Fetal_Head_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Fetal_Head_yolov11-m_640x640_best.pt")
    elif task == "Fetal_NT":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Fetal_NT_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Fetal_NT_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Fetal_NT_yolov11-m_640x640_best.pt")
    elif task == "Thyroid_Gland":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Thyroid_Gland_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Thyroid_Gland_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Thyroid_Gland_yolov11-m_640x640_best.pt")
    elif task == "Thyroid_Nudule":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Thyroid_Nudule_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Thyroid_Nudule_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Thyroid_Nudule_yolov11-m_640x640_best.pt")
    else:
        raise ValueError(f"Unsupported task: {task}. Supported tasks are: "
                         "Breast_Nudule, carotid_artery, Fetal_Abdomen, Fetal_Head, Fetal_NT, Thyroid_Gland, Thyroid_Nudule.")

    model = YOLO(pth_path)
    model.to(device)
    yolo11_detect_predict(input_path=input,
                          output_path=output if output else input,
                          model_weight=pth_path,
                          conf=0.4,
                          iou=0.45)  # IoU threshold
