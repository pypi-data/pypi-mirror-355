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
        return os.path.join(output_dir, "downloaded_file.pth.tar")
    # Create target directory 
    file_path = os.path.join(output_dir, "downloaded_file.pth.tar")
    os.makedirs(output_dir, exist_ok=True)

    # Get the number of split files
    num_parts = len(url)

    # Download and save each split file 
    for i in range(num_parts):
        print(f"Starting to download split file {i + 1}/{num_parts}: {url[i]}")
        try:
            # Download file 
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


    return file_path


def pred(input: Union[str, Path], output: Union[str, Path], task: str, device: str = "cuda"):
    """
    Ultrasegmentator API for nnUNet inference.
    :param input:
    :param output:
    :param task: str, one of the following:"ALL_planes", "Breast_Nodule", "Thyroid_Nodule",
    :return:
    """
    skip_saving = False

    if validate_device_type_api(device):
        device = torch.device(convert_device_to_cuda(device))

    cache_dir = get_cache_dir()
    if task == "All_Planes":
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
        label_dict = {0: "Breast_Nodule",1: "Heart",2: "Fetal_abdomen",3: "Fetal_Head",4: "Fetal_NT",5: "Thyroid_or_Caroid"}
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


    if skip_saving:
        output = None
    else:
        if output is not None and not os.path.exists(output):
            os.makedirs(output, exist_ok=True)

    model = timm.create_model(
        'timm/convnext_base.clip_laion2b_augreg_ft_in1k',
        num_classes=len(label_dict),
        in_chans=3,
        pretrained=False,
        checkpoint_path=cache_dir,
    )
    model.to(device)
    model = model.eval()

    image_name_list = os.listdir(input)

    for image_name in image_name_list:
        image_path = os.path.join(input, image_name)
        img = Image.open(image_path).convert('RGB')

        with torch.no_grad():
            # get model specific transforms (normalization, resize)
            data_config = timm.data.resolve_model_data_config(model)
            transforms = timm.data.create_transform(**data_config, is_training=False)

            output_ = model(transforms(img).unsqueeze(0).to(device))
            output_ = output_.softmax(-1).squeeze(0)
            pred_idx = torch.argmax(output_, dim=-1).cpu().numpy().item()
            result = {
                "image": image_name,
                "label": label_dict[pred_idx],
                "score": float(output_[pred_idx]),
            }

            with open(os.path.join(output, image_name.split(".")[0] + ".json"), 'w') as f:
                json.dump(result, f, indent=4)


def main():

    parser = argparse.ArgumentParser(
        description="Ultraclassifier: Medical Ultrasound image classification tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-i", "--input", required=True,
                        help="Input file/directory path (must be a valid existing path)")
    parser.add_argument("-o", "--output", required=True,
                        help="Output directory path (required for saving results)")

    parser.add_argument("-t", "--task", required=True,
                        help=f"Segmentation task name. Supported: ALL_planes,Thyroid_Nodule, Breast_Nodule")
    parser.add_argument("-d", "--device", default="gpu:1",
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
