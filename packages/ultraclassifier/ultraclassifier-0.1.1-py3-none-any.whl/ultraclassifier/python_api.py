import argparse
import json
import sys
import os
import zipfile
from pathlib import Path
from PIL import Image
import timm

import numpy as np
import urllib
import torch
import re

from pathlib import Path
from typing import Union


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
        return os.path.join(output_dir, "downloaded_file.pth.tar")
    # 创建目标目录
    file_path = os.path.join(output_dir, "downloaded_file.pth.tar")
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


    return file_path


# https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaa
# https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaa
# https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaa

#ALL_planes, Breast_Nodule, Thyroid_Nodule

def pred(input: Union[str, Path], output: Union[str, Path, None] = None, task: str = "ALL_planes", device: str = "cuda"):
    """
    Ultrasegmentator API for nnUNet inference.
    :param input:
    :param output:
    :param task: str, one of the following:"ALL_planes", "Breast_Nodule", "Thyroid_Nodule",
    :return:
    """
    skip_saving = False

    # 处理设备参数
    device = torch.device('cuda') if device == "gpu" else torch.device('cpu')
    cache_dir = get_cache_dir()
    if task == "ALL_planes":
        url_list = [
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaa',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partab',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partac',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partad',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partae',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaf',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_3/releases/download/v1.0.0/All_Planes_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partag',
        ]
        cache_dir = os.path.join(cache_dir, "All_Planes")
        cache_dir  = download_and_unzip_parts(url_list, cache_dir)
        label_dict = {0: "Breast_Nodule",1: "Heart",2: "Fetal_abdomen",3: "Fetal_Head",4: "Fetal_NT",5: "thyroid_caroid_nodule"}
    elif task == "Breast_Nodule":
        url_list = [
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaa',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partab',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partac',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partad',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partae',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaf',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_4/releases/download/v1.0.0/Breast_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partag',
        ]
        cache_dir = os.path.join(cache_dir, "Breast_Nodule")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
        label_dict ={0:"benign", 1:"Malignant", 2:"normal"}
    elif task == "Thyroid_Nodule":
        url_list = [
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaa',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partab',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partac',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partad',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partae',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partaf',
            'https://gitee.com/Jacksonyu123/ultrasound_tool_5/releases/download/v1.0.0/Thyroid_Nodule_convnext_base_clip_laion2b_augreg_ft_in1k_256%C3%97256.partag',
        ]
        cache_dir = os.path.join(cache_dir, "Thyroid_Nodule")
        cache_dir = download_and_unzip_parts(url_list, cache_dir)
        label_dict ={0:"benign", 1:"Malignant"}
    else:
        raise ValueError(f"Unsupported task: {task}. Supported tasks are: CAMUS_Left_Heart, Four_Chamber_Heart.")

    # 处理输出路径
    if skip_saving:
        output = None
    else:
        if output is None and not os.path.exists(output):
            output.mkdir(parents=True, exist_ok=True)

    image_name_list = os.listdir(input)

    for image_name in image_name_list:
        image_path = os.path.join(input, image_name)
        img = Image.open(image_path).convert('RGB')

        model = timm.create_model(
            'timm/convnext_base.clip_laion2b_augreg_ft_in1k',
            num_classes=len(label_dict),
            in_chans=3,
            pretrained=False,
            checkpoint_path=cache_dir,
        )
        model.to(device)
        model = model.eval()

        with torch.no_grad():
            # get model specific transforms (normalization, resize)
            data_config = timm.data.resolve_model_data_config(model)
            transforms = timm.data.create_transform(**data_config, is_training=False)

            output_ = model(transforms(img).unsqueeze(0))  # unsqueeze single image into batch of 1
            output_ = output_.softmax(-1).squeeze(0)
            pred_idx = torch.argmax(output_, dim=-1).cpu().numpy().item()
            result = {
                "image": image_name,
                "label": label_dict[pred_idx],
                "score": float(output_[pred_idx]),
            }
            print(result)
            with open(os.path.join(output, image_name.split(".")[0] + ".json"), 'w') as f:
                json.dump(result, f, indent=4)


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
    parser.add_argument("-t", "--task", required=True,
                        help=f"Segmentation task name. Supported: CAMUS_Left_Heart, Four_Chamber_Heart, Carotid_Artery, "
                             f"Thyroid_Nodule, Thyroid_Gland, Fetal_Head, Fetal_Abdomen, Breast_Nodule")
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
