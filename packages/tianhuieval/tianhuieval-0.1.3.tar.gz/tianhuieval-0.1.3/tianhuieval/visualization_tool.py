import os
import numpy as np
import pandas as pd
import cv2
import json
import matplotlib.pyplot as plt
from IPython.display import HTML
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon, MultiPolygon
import pickle
import base64
import rasterio
import random
from rasterio.features import geometry_mask
import re
from skimage.color import rgb2gray, gray2rgb
from pycocotools import mask as maskUtils
import torch
from typing import List, Optional, Tuple, Union


def overlay_masks(
    image_path: str,
    mask_paths: List[str],
    colors: Optional[List[Tuple[int, int, int]]] = None,
    alpha: float = 0.5,
    return_type: str = "array",  # "display" or "array"
) -> Union[None, np.ndarray]:
    """
    Overlay multiple masks on an image using OpenCV.

    Args:
        image_path (str): Path to the input image.
        mask_paths (List[str]): List of paths to mask images.
        colors (Optional[List[Tuple[int, int, int]]]): List of BGR colors (e.g., [(0, 0, 255)] for red).
            If None, random colors are used.
        alpha (float): Transparency of masks (0.0 to 1.0).
        return_type (str): "display" to show the result or "array" to return the blended image.

    Returns:
        If return_type="array", returns the blended image (BGR format). If "display", shows the image.
    """
    # Read the image (BGR format in OpenCV)
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Initialize overlay (same size as image)
    overlay = np.zeros_like(image)

    # Generate random colors if not provided
    if colors is None:
        colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(len(mask_paths))
        ]
    elif len(colors) < len(mask_paths):
        raise ValueError("Number of colors must match number of masks.")

    random_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # Process each mask
    for mask_path, color in zip(mask_paths, colors):
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)  # Read as grayscale
        if mask is None:
            raise FileNotFoundError(f"Mask not found at {mask_path}")

        # Apply color to the mask region
        overlay[mask > 0] = color
        # overlay[mask > 200] = random_color

    # Blend image and overlay
    blended = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)

    # Return or display
    if return_type == "display":
        cv2.imshow("Overlay Result", blended)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    elif return_type == "array":
        return blended
    else:
        raise ValueError('return_type must be "display" or "array".')
        
# string形式的polygon转为mask进行可视化依赖的函数
def str2object(json_string):
    # 把str反序列化成对象
    '''
    将json中polygon的string形式转为polygon对象
    '''
    pickled_bytes = base64.b64decode(json_string.encode("utf-8"))
    obj = pickle.loads(pickled_bytes)
    return obj

def polygon2mask(multi_polygon,height,width):
    '''
    将polygon对象转为mask
    '''
    height, width = height, width  # 掩码的高度和宽度
    transform = rasterio.transform.from_origin(0, height, 1, 1)

    # 将 MultiPolygon 转换为掩码
    mask = geometry_mask(
        [multi_polygon],
        transform=transform,
        out_shape=(height, width),
        invert=True
    )
    return mask


def polygon_to_mask(polygon, image_height, image_width):
    # 这是一个已经忘了输入的polygon需要是什么形式的polygon转mask函数
    # Create an empty mask
    mask = np.zeros((image_height, image_width), dtype=np.uint8)
    
    # Create a COCO-style RLE (Run-Length Encoding) mask from polygon
    rle = maskUtils.frPyObjects(polygon, image_height, image_width)
    
    # Decode the RLE mask to binary mask
    mask = maskUtils.decode(rle)
    
    return mask

def load_json(json_file):
    # 加载json文件
    with open(json_file) as f:
        data = json.load(f)
    return data

def scale_polygon_coordinates(masks, width, height, scale=1000):
    """
    将多边形坐标的每个值乘以指定的缩放因子。

    :param points: (x, y) 元组列表
    :param scale_factor: 缩放因子
    :return: 缩放后的 (x, y) 元组列表
    """

    scaled_masks = [[(x / scale * width, y / scale * height) for x, y in group] for group in masks]
    return scaled_masks


class CoordinatesQuantizer(object):
    """
    Quantize coornidates (Nx2)
    """

    def __init__(self, mode, bins):
        self.mode = mode
        self.bins = bins

    def quantize(self, coordinates: torch.Tensor, size):
        bins_w, bins_h = self.bins  # Quantization bins.
        size_w, size_h = size       # Original image size.
        size_per_bin_w = size_w / bins_w
        size_per_bin_h = size_h / bins_h
        assert coordinates.shape[-1] == 2, 'coordinates should be shape (N, 2)'
        x, y = coordinates.split(1, dim=-1)  # Shape: 4 * [N, 1].

        if self.mode == 'floor':
            quantized_x = (x / size_per_bin_w).floor().clamp(0, bins_w - 1)
            quantized_y = (y / size_per_bin_h).floor().clamp(0, bins_h - 1)

        elif self.mode == 'round':
            raise NotImplementedError()

        else:
            raise ValueError('Incorrect quantization type.')

        quantized_coordinates = torch.cat(
            (quantized_x, quantized_y), dim=-1
        ).int()

        return quantized_coordinates

    def dequantize(self, coordinates: torch.Tensor, size):
        bins_w, bins_h = self.bins  # Quantization bins.
        size_w, size_h = size       # Original image size.
        size_per_bin_w = size_w / bins_w
        size_per_bin_h = size_h / bins_h
        assert coordinates.shape[-1] == 2, 'coordinates should be shape (N, 2)'
        x, y = coordinates.split(1, dim=-1)  # Shape: 4 * [N, 1].

        if self.mode == 'floor':
            # Add 0.5 to use the center position of the bin as the coordinate.
            dequantized_x = (x + 0.5) * size_per_bin_w
            dequantized_y = (y + 0.5) * size_per_bin_h

        elif self.mode == 'round':
            raise NotImplementedError()

        else:
            raise ValueError('Incorrect quantization type.')

        dequantized_coordinates = torch.cat(
            (dequantized_x, dequantized_y), dim=-1
        )

        return dequantized_coordinates

def extract_polygons(generated_text, image_size):
    polygon_start_token='<poly>'
    polygon_end_token='</poly>'
    polygon_sep_token='<sep>'
    with_box_at_start=False
    coordinates_quantizer = CoordinatesQuantizer('floor', (1000, 1000),)
    polygons_instance_pattern = rf'{re.escape(polygon_start_token)}(.*?){re.escape(polygon_end_token)}'
    polygons_instances_parsed = list(re.finditer(polygons_instance_pattern, generated_text))
    # polygons = list(re.findall(polygons_instance_pattern, generated_text))
    # extracted_values = [match for match in polygons]
    box_pattern =  rf'((?:<\d+>)+)(?:{re.escape(polygon_sep_token)}|$)'
    all_polygons = []
    for _polygons_instances_parsed in polygons_instances_parsed:
        # Prepare instance.
        instance = {}
    
        # polygons_parsed= list(re.finditer(box_pattern, phrase_text))
        if isinstance(_polygons_instances_parsed, str): 
            polygons_parsed= list(re.finditer(box_pattern, _polygons_instances_parsed))
        else:
            polygons_parsed= list(re.finditer(box_pattern, _polygons_instances_parsed.group(1)))
        if len(polygons_parsed) == 0:
            continue
    
        # a list of list (polygon)
        bbox = []
        polygons = []
        for _polygon_parsed in polygons_parsed:
            # group 1: whole <\d+>...</\d+>
            _polygon = _polygon_parsed.group(1)
            # parse into list of int
            _polygon = [int(_loc_parsed.group(1)) for _loc_parsed in re.finditer(r'<(\d+)>', _polygon)]
            if with_box_at_start and len(bbox) == 0:
                if len(_polygon) > 4:
                    # no valid bbox prediction
                    bbox = _polygon[:4]
                    _polygon = _polygon[4:]
                else:
                    bbox = [0, 0, 0, 0]
            # abandon last element if is not paired 
            if len(_polygon) % 2 == 1:
                _polygon = _polygon[:-1]
            # reshape into (n, 2)
            _polygon = coordinates_quantizer.dequantize(
                torch.tensor(np.array(_polygon).reshape(-1, 2)),
                size=image_size
            ).reshape(-1).tolist()
            # reshape back
            if len(_polygon)>=6:
                polygons.append(_polygon)
        if polygons != []:
            all_polygons.append(polygons)
    return all_polygons


def extract_roi (input_string, pattern = r"\{<(\d+)><(\d+)><(\d+)><(\d+)>\|<(\d+)>"):
    '''
    <box>...</box>
    
    '''
    # Regular expression pattern to capture the required groups
    pattern = pattern
    # Find all matches
    matches = re.findall(pattern, input_string)
    print(matches)
    
    # Extract the values
    extracted_values = [match for match in matches]
    print(extracted_values)

    return extracted_values

def merge_mask_show(image_array,obj_anns):
    '''
    将obj_anns中的所有标注对象显示在原图中, string形式的polygon
    其中obj_anns为json标注文件里的目标标注，标注形式为string类型的polygon
    依赖函数：str2object，polygon2mask
    '''
    fused_mask = np.zeros(image_array.shape)
    highlighted_image = image_array.copy()
    obj_num = len(obj_anns)
    print(obj_num)
    # 显示结果
    plt.figure(figsize=(24, 16))
    for obj_ann in obj_anns: 
        obj_str = obj_ann['segmentation']
        multi_polygon = str2object(obj_str)
        height = image_array.shape[0]
        width = image_array.shape[1]
        mask = polygon2mask(multi_polygon,height,width)

        # 上下翻转掩模
        flipped_mask = np.flipud(mask)
#         random_color = random.choice(COLORS)
        random_color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
        fused_mask[flipped_mask] = random_color
        highlighted_image[flipped_mask] = random_color   # 直接在image上覆盖mask
       
    mask = fused_mask.astype(np.uint8)
    # 设置透明度
    alpha = 0.5  # mask 的透明度
    overlay = cv2.addWeighted(image_array, 1, mask, alpha, 0)   # 通过一定透明度叠加mask和image
    # cv2.addWeighted的形式似乎会alpha无法设置成全透明，也会改变图像的色调
    plt.subplot(2,2,1)
    plt.imshow(overlay)
    plt.title('Overlap with mask')
    plt.axis('off')
    plt.subplot(2,2,2)
    plt.imshow(image_array)
    plt.title('Original Image')
    plt.axis('off')
    plt.tight_layout()
    plt.subplot(2,2,3)
    plt.imshow(mask)
    plt.title('Mask')
    plt.axis('off')
    plt.tight_layout()
    plt.subplot(2,2,4)
    plt.imshow(highlighted_image)
    plt.title('Image with mask')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def change_polylist(ori_polygons):
    '''
    把list类型的polygon形式进行转换为坐标对形式
    输入ori_polygons形式：[[[x11,y11,x12,y12],[x21,y21,x22,y22,x23,y23]...,...[]]]
    输出（x,y）元祖列表，masks形式：[[(x11,y11),(x12,y12)],[(x21,y21),(x22,y22),(x23,y23)]...,...[(,)]]
    '''
    polygons = [points for sublist in ori_polygons for points in sublist]
    masks = []
    for points in polygons:
        mask = list(zip(points[::2], points[1::2]))
        masks.append(mask)
    return masks

def show_image_pair(image1,image2):
    # 成对展示图像
    plt.figure()
    plt.subplot(1,2,1)
    show_one_image(image1,'image1')
    plt.subplot(1,2,2)
    show_one_image(image2,'image2')
    plt.show()
    
def show_one_image(image,title):
    image = np.array(image)
    plt.imshow(image)
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    
def visualize_boxes(image,bboxes,bbox_type='hbb',color=(0, 255, 0)):
    '''
    绘制检测框、多边形框，bbox_type可为'hbb','obb','polygon'
    输入为图像，list类型的bboxes(实际坐标值)，以及bbox的类型：hbb或者obb或者polygon
    '''
    show_img = np.array(image)
    if bbox_type == 'hbb':
        for bbox in bboxes:
            cv2.rectangle(show_img, (int(bbox[0]), int(bbox[1])), 
                              (int(bbox[2]), int(bbox[3])), color, 2)
    elif bbox_type == 'obb' or bbox_type == 'polygon':
        for bbox in bboxes:
            pts = np.array(bbox,np.int32).reshape((-1,1,2))
            cv2.polylines(show_img, [pts], isClosed=True, color=color, thickness=2)
    plt.imshow(show_img)
    plt.axis('off')
    plt.show()


def parse_polygon_coordinates(poly_string):
    """
        解析多边形坐标字符串，并将其转换为 (x, y) 元组列表。

        :param poly_string: 多边形坐标字符串，格式为 <poly><x1><y1><x2><y2>...</poly>
        :return: (x, y) 元组列表
        """
    # 使用正则表达式提取所有坐标
    pattern = r'<poly>(.*?)</poly>'
    matches = re.findall(pattern, poly_string)
#     print(matches)

    if not matches:
        raise ValueError("Invalid polygon coordinate format")

    # 检查坐标数量是否为偶数
    #if len(matches) % 2 != 0:
    #    raise ValueError("Invalid number of coordinates")

    masks = []
    for match in matches:
        # 提取所有的数字
        numbers = list(map(int, re.findall(r'\d+', match)))
        # 每两个数字组成一个元组
        mask = list(zip(numbers[::2], numbers[1::2]))
        masks.append(mask)

    return masks

def draw_text(draw,text,polygon,font,color):
    # Centroid formula: (x, y) = (sum(x_coords) / n, sum(y_coords) / n)
#             x_coords = [point[0] for point in polygon]
#             y_coords = [point[1] for point in polygon]
#             centroid_x = sum(x_coords) // len(polygon)
#             centroid_y = sum(y_coords) // len(polygon)
    # Prepare text and calculate size
    text_bbox = font.getbbox(text)  # Use getbbox() to get text size
    text_width, text_height = text_bbox[2], text_bbox[3]

    # Calculate position for text background
    text_position = (polygon[0][0], polygon[0][1] - text_height - 5)  # Above the first point               
    # Adjust the text position to center it
    text_background = [
        text_position,
        (text_position[0] + text_width + 5, text_position[1] + text_height + 5),
    ]

    # Draw text background
    draw.rectangle(text_background, fill=color)
    # Draw the label text
    draw.text((text_position[0] + 2, text_position[1] + 2), text, fill="white", font=font)
    return draw
    
def draw_polygons(image,gt_masks,gt_color,pred_masks=[],pred_color=(0,255,0),text='',fill=True):
    '''
    输入是（x,y）元祖列表，形式：[[(x11,y11),(x12,y12)],[(x21,y21),(x22,y22),(x23,y23)]...,...[(,)]]
    只画一类标注（不同时画pred和gt），
    且每个polygon的文本是一样的，也可以把text改成list和polygon的list对应
    '''
#     print(image.width,image.height)
    # show_img = draw_polygons_v2(image, masks, pred_colors)

    image = image.convert("RGBA")

    # 创建一个与原图同样大小的透明图像层
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
#     draw = ImageDraw.Draw(image)

    if text != '':
        # Specify a font with a larger size (Linux-specific)
        try:
            # Change this to an appropriate path to a font on your Linux system
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font = ImageFont.truetype(font_path, 10)  # Adjust font size here  # 20 for seg, 10 for change det
        except Exception as e:
            print("Font not found or unable to load, using default font.")
            font = ImageFont.load_default()

    # 绘制每个mask
    for i, mask in enumerate(gt_masks):
        # 将mask数据转换为适合绘制的格式
        polygon = [tuple(map(int, point)) for point in mask]
        # 绘制多边形
        # draw.polygon(polygon, fill=pred_color)
        draw.polygon(polygon, fill=gt_color+(80,), width=2) if fill else draw.polygon(polygon, outline=gt_color, width=2)
        if text != '':  
            draw = draw_text(draw,text,polygon,font,gt_color)
    
    if pred_masks!=[]:
        for i, mask in enumerate(pred_masks):
            # 将mask数据转换为适合绘制的格式
            polygon = [tuple(map(int, point)) for point in mask]
            # 绘制多边形
            # draw.polygon(polygon, fill=pred_color)
            draw.polygon(polygon, fill=pred_color+(80,), width=2) if fill else draw.polygon(polygon, outline=pred_color, width=2)
    result = Image.alpha_composite(image, overlay)
    
    return result