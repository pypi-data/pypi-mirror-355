import argparse
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


def download_file(url: str, file_path) -> Path:
    """
    Download the file to the cache directory (if it does not exist).
    Returns the full path to the downloaded file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Check if the file already exists
    if os.path.exists(file_path):
        print(f"File already exists, skipping download: {file_path}")
        return file_path

    print(f"Starting download: {url}")
    try:
        # Download the file
        urllib.request.urlretrieve(url, file_path)
        print(f"File saved to: {file_path}")
        return file_path
    except Exception as e:
        # Clean up potentially created empty file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise RuntimeError(f"Download failed: {e}") from e


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


def pred(input: Union[str, Path], output: Union[str, Path], task: str , device: str = "gpu") -> None:
    """
    Ultrasegmentator API for medical ultrasound image detection.
    :param input: Input file/directory path (must be a valid existing path)
    :param output: Output directory path (required for saving results)
    :param task: str, one of the following: "Breast_Nodule", "carotid_artery", "Fetal_Abdomen", "Fetal_Head", "Fetal_NT", "Thyroid_Gland", "Thyroid_Nodule"
    :param device: "gpu" or "cpu" or "mps" or "gpu:X" where X is the GPU device ID
    :return: None
    """
    # 处理设备参数
    if validate_device_type_api(device):
        device = torch.device(convert_device_to_cuda(device))

    cache_dir = get_cache_dir()
    # 检查模型路径是否存在，如果不存在则下载
    if task == "CAMUS_Left_Heart":
        model_url = "https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.1/CAMUS_Left_Heart_yolov11-m_384%C3%97384_best.pt"
        download_file(model_url, os.path.join(cache_dir, "CAMUS_Left_Heart_yolov11-m_384x384_best.pt"))
        pth_path = os.path.join(cache_dir, "CAMUS_Left_Heart_yolov11-m_384x384_best.pt")
    elif task == "Breast_Nodule":
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
    elif task == "Thyroid_Nodule":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Thyroid_Nudule_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Thyroid_Nudule_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Thyroid_Nudule_yolov11-m_640x640_best.pt")
    elif task == 'Four_Chamber_Heart':
        model_url = "https://gitee.com/Jacksonyu123/ultrasound_tool/releases/download/v1.0.1/Four_Chamber_Heart_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Four_Chamber_Heart_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Four_Chamber_Heart_yolov11-m_640x640_best.pt")
    else:
        raise ValueError(f"Unsupported task: {task}. Supported tasks are: "
                         "Breast_Nudule, carotid_artery, Fetal_Abdomen, Fetal_Head, Fetal_NT, Thyroid_Gland, Thyroid_Nudule.")

    # 处理输出路径
    if not os.path.exists(output):
        output.mkdir(parents=True, exist_ok=True)

    model = YOLO(pth_path)
    model.to(device)
    yolo11_detect_predict(input_path=input,
                          output_path=output if output else input,
                          model_weight=pth_path,
                          conf=0.4,
                          iou=0.45)  # IoU threshold


def main():

    parser = argparse.ArgumentParser(
        description="Ultradetector: Medical Ultrasound image detection tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-i", "--input", required=True,
                        help="Input file/directory path (must be a valid existing path)")
    parser.add_argument("-o", "--output", required=True,
                        help="Output directory path (required for saving results)")
    parser.add_argument("-t", "--task", required=True,
                        help=f"Detection task name. Supported: CAMUS_Left_Heart, Four_Chamber_Heart, Carotid_Artery, "
                             f"Thyroid_Nodule, Thyroid_Gland, Fetal_Head, Fetal_Abdomen, Breast_Nodule")
    parser.add_argument("-d", "--device", default="cuda",
                        help="Computation device. Options: 'gpu', 'cpu', 'mps' or 'gpu:X' (X is GPU ID)")

    args = parser.parse_args()

    pred(
        input=args.input,
        output=args.output,
        task=args.task,
        device=args.device
    )


if __name__ == "__main__":
    main()
