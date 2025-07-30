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
    if task == "Breast_Nudule":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Breast_Nudule_yolov11-m_640%C3%97640_best.pt"  # 替换为实际的模型下载链接
        download_file(model_url, os.path.join(cache_dir, "Breast_Nudule_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Breast_Nudule_yolov11-m_640x640_best.pt")
    elif task == "carotid_artery":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/carotid_artery_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "carotid_artery_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "carotid_artery_yolov11-m_640x640_best.pt")
    elif task == "Fetal_Abdomen":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Fetal_Abdomen_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Fetal_Abdomen_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Fetal_Abdomen_yolov11-m_640x640_best.pt")
    elif task == "Fetal_Head":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Fetal_Head_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Fetal_Head_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Fetal_Head_yolov11-m_640x640_best.pt")
    elif task == "Fetal_NT":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Fetal_NT_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Fetal_NT_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Fetal_NT_yolov11-m_640x640_best.pt")
    elif task == "Thyroid_Gland":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Thyroid_Gland_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Thyroid_Gland_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Thyroid_Gland_yolov11-m_640x640_best.pt")
    elif task == "Thyroid_Nudule":
        model_url = "https://gitee.com/jacksonyu123/ultrasound_tool/releases/download/v1.0.0/Thyroid_Nudule_yolov11-m_640%C3%97640_best.pt"
        download_file(model_url, os.path.join(cache_dir, "Thyroid_Nudule_yolov11-m_640x640_best.pt"))
        pth_path = os.path.join(cache_dir, "Thyroid_Nudule_yolov11-m_640x640_best.pt")
    else:
        raise ValueError(f"Unsupported task: {task}. Supported tasks are: "
                         "Breast_Nudule, carotid_artery, Fetal_Abdomen, Fetal_Head, Fetal_NT, Thyroid_Gland, Thyroid_Nudule.")

    model = YOLO(pth_path)
    model.to(device)
    pth_path = [pth_path]

    img_path_list = os.listdir(input)

    date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    save_path = os.path.join(output, date)

    num = 0

    for img_temp_path in img_path_list:
        try:
            # save_path = os.path.join(output, datetime.now().strftime("%Y%m%d-%H%M%S"))
            img_path = input + '/' + img_temp_path
            # frame_list = os.listdir(frame_folder_path)
            # os.makedirs(save_path + '/' + 'ori_Frames' +'/'+ frame_folder,exist_ok=True)
            os.makedirs(save_path + '/' + 'vis', exist_ok=True)
            os.makedirs(save_path + '/' + 'Jsons', exist_ok=True)
            os.makedirs(save_path + '/' + 'Diss', exist_ok=True)
            os.makedirs(save_path + '/' + 'Boxes', exist_ok=True)
            os.makedirs(save_path + '/' + 'Speed', exist_ok=True)
            # for frame_name in frame_list:
            #     frame_path = frame_folder_path + '/' + frame_name

            results = model.predict(source=img_path, imgsz=640, batch=1)

            ori_img = cv2.imread(img_path)

            h, w, _ = ori_img.shape

            speed = [float(results[0].speed['preprocess'] + results[0].speed['inference'] + results[0].speed['postprocess']) / 1000]
            keypoints_list_ = results[0].keypoints.data.detach().cpu().numpy().tolist()
            keypoints_list = []

            keypoints_list.append(keypoints_list_[0][0])
            keypoints_list.append(keypoints_list_[1][0])

            cv2.circle(ori_img, (int(keypoints_list[0][0]), int(keypoints_list[0][1])), 5, (0, 0, 255), -1)
            cv2.circle(ori_img, (int(keypoints_list[1][0]), int(keypoints_list[1][1])), 5, (0, 255, 0), -1)

            distance = []
            distance.append(float(np.sqrt((keypoints_list[0][0] - keypoints_list[1][0]) ** 2 + (keypoints_list[0][1] - keypoints_list[1][1]) ** 2)))
            keypoints_list = [[keypoints_list[0][0] / w, keypoints_list[0][1] / h],
                              [keypoints_list[1][0] / w, keypoints_list[1][1] / h]]
            boxes_list = results[0].boxes.xywhn.detach().cpu().numpy().tolist()

            for i in range(len(boxes_list)):
                x_center, y_center, width, height = boxes_list[i]
                xmin = int((x_center - width / 2) * w)
                ymin = int((y_center - height / 2) * h)
                xmax = int((x_center + width / 2) * w)
                ymax = int((y_center + height / 2) * h)

                # 绘制矩形框
                if i == 0:
                    color = (255, 255, 0)  # 绿色
                else:
                    color = (0, 255, 255)
                thickness = 2
                cv2.rectangle(ori_img, (xmin, ymin), (xmax, ymax), color, thickness)

            cv2.imwrite(save_path + '/' + 'vis/' + img_path.split('/')[-1], ori_img)
            with open(save_path + '/Jsons/' + img_path.split('/')[-1].split('.')[0] + '.json', 'w') as f1:
                json.dump(keypoints_list, f1)
            with open(save_path + '/Diss/' + img_path.split('/')[-1].split('.')[0] + '.json', 'w') as f2:
                json.dump(distance, f2)
            with open(save_path + '/Boxes/' + img_path.split('/')[-1].split('.')[0] + '.json', 'w') as f3:
                json.dump(boxes_list[0], f3)
            with open(save_path + '/Speed/' + img_path.split('/')[-1].split('.')[0] + '.json', 'w') as f4:
                json.dump(speed, f4)
            num += 1
        except:
            print('*' * 100)
            print(img_path)
            print('*' * 100)
    pth_path.append(num)
    print(num)
    with open(save_path + '/' + 'pth_path.json', 'w') as f2:
        json.dump(pth_path, f2)
    # # 如果要可视化一些预测结果，可以在这里添加可视化代码
