import os

import numpy as np
from pycocotools import mask as maskUtils
from pycocotools import mask
from skimage import measure
import json


def format_polygon(polygon):
    """ Format the polygon points from [x1, y1, x2, y2, ...] to [(x1, y1), (x2, y2), ...] """
    return [(polygon[i], polygon[i + 1]) for i in range(0, len(polygon), 2)]

def polygon_to_mask(polygon):
    """ Convert a polygon in the given format to a binary mask """
    x_coords = polygon[::2]  # Extract x coordinates (every other element)
    y_coords = polygon[1::2]  # Extract y coordinates (the rest)
    
    # Determine the bounding box (min and max values of x and y)
    min_x, max_x = int(min(x_coords)), int(max(x_coords))
    min_y, max_y = int(min(y_coords)), int(max(y_coords))
    
    # Define the mask size based on the bounding box
    mask_width = max_x - min_x + 1
    mask_height = max_y - min_y + 1
    
    # Create an empty mask with the bounding box size
    mask = np.zeros((mask_height, mask_width), dtype=np.uint8)
    
    # Flatten polygon points and adjust them to the bounding box
    adjusted_polygon = [(x - min_x, y - min_y) for x, y in format_polygon(polygon)]
    flat_polygon = np.array(adjusted_polygon).flatten().tolist()  # Flatten the 2D list
    
    # Create a COCO-style RLE mask from the adjusted polygon
    rle = maskUtils.frPyObjects([flat_polygon], mask_height, mask_width)  # Wrap flat_polygon in a list
    
    # Decode the RLE mask to a binary mask
    mask = maskUtils.decode(rle)
    
    return mask, (min_x, min_y, mask_width, mask_height)


def polygon_to_mask(polygon, image_height, image_width):
    # Create an empty mask
    mask = np.zeros((int(image_height), int(image_width)), dtype=np.uint8)
    
    # Create a COCO-style RLE mask from polygon

    rle = maskUtils.frPyObjects([polygon], image_height, image_width)

    
    # Decode the RLE mask to binary mask
    mask = maskUtils.decode(rle)
    
    return mask
    
def resize_mask(mask, target_size):
    """ Resize a binary mask to the target size """
    return cv2.resize(mask, target_size, interpolation=cv2.INTER_NEAREST)


def find_best_matches(masks1, masks2, threshold=0.1):
    """ 
    Find the best matching mask pairs between two sets of masks based on Dice coefficient. 
    If no match exceeds the threshold, set the Dice score to 0 (over-segmentation).
    """
    n = len(masks1)
    m = len(masks2)
    
    # Calculate all pairwise Dice coefficients
    dice_matrix = np.zeros((n, m))
    
    for i, mask1 in enumerate(masks1):
        for j, mask2 in enumerate(masks2):
            dice_matrix[i, j] = dice_coefficient(mask1, mask2)
    
    # Initialize matched sets and dice scores
    matched_pairs = []
    unmatched_masks1 = set(range(n))  # Indices of masks in set 1
    unmatched_masks2 = set(range(m))  # Indices of masks in set 2
    dice_scores = []

    # For each mask in set 1, find the best match in set 2
    for i in range(n):
        best_j = np.argmax(dice_matrix[i, :])  # Best match in set 2 for mask i
        best_score = dice_matrix[i, best_j]

        if best_score > threshold:
            # If a good match is found, record it and remove from unmatched sets
            matched_pairs.append((i, best_j))
            dice_scores.append(best_score)
            unmatched_masks1.discard(i)
            unmatched_masks2.discard(best_j)
        else:
            # No good match found, assign Dice score of 0 (over-segmentation)
            dice_scores.append(0.0)

    # Handle unmatched masks from both sets (over/under-segmentation)
    for i in unmatched_masks1:
        dice_scores.append(0.0)  # Masks in set 1 with no match in set 2
    for j in unmatched_masks2:
        dice_scores.append(0.0)  # Masks in set 2 with no match in set 1

    return dice_scores, matched_pairs


def dice_coefficient(mask1, mask2):
    """ Calculate the Dice coefficient between two binary masks """
    intersection = np.sum(mask1 * mask2)
    total_area = np.sum(mask1) + np.sum(mask2)
    
    if total_area == 0:
        return 1.0  # Avoid division by zero if both masks are empty
    return 2 * intersection / total_area

def iou_score(mask1, mask2):
    """ Calculate the Intersection over Union (IoU) between two binary masks """
    intersection = np.sum(mask1 * mask2)
    union = np.sum(mask1) + np.sum(mask2) - intersection
    
    if union == 0:
        return 1.0  # Avoid division by zero if both masks are empty
    return intersection / union

def vc_score(mask1, mask2, volume_diff_t = 0.08):
    """ Calculate the Volume Consistency (VC_8) between two binary masks """
    volume1 = np.sum(mask1)
    volume2 = np.sum(mask2)
    
    if volume1 == 0 and volume2 == 0:
        return 1.0  # Both volumes are empty
    
    volume_diff = np.abs(volume1 - volume2)
    avg_volume = (volume1 + volume2) / 2.0
    
    # Check if the volume difference is within 8% of the average volume
    return 1.0 if volume_diff <= volume_diff_t * avg_volume else 0.0


def merge_masks(masks):
    """
    Merge all masks into one by using logical OR operation.
    This creates a single binary mask that combines all the input masks.
    """
    merged_mask = np.zeros_like(masks[0], dtype=np.uint8)  # Initialize an empty mask with the same size
    
    for mask in masks:
        merged_mask = np.logical_or(merged_mask, mask)  # Merge masks using OR operation
    
    return merged_mask.astype(np.uint8)

def calculate_merged(masks1, masks2):
    """
    Merge all GT masks and result masks, then calculate the Dice coefficient
    between the two merged masks.
    """
    # Merge all GT masks into one
    merged_gt = merge_masks(masks1)
    
    # Merge all result masks into one
    merged_result = merge_masks(masks2)
    
    # Calculate the Dice coefficient between the merged masks
    dice = dice_coefficient(merged_gt, merged_result)
    iou = iou_score(merged_gt, merged_result)
    vc8 = vc_score(merged_gt, merged_result, volume_diff_t=0.08)
    vc16 = vc_score(merged_gt, merged_result, volume_diff_t=0.16)
    
    return dice, iou, vc8, vc16

def load_mask_from_path(mask_path):
    return mask

def evaluate_segmentation(y_true, y_pred, crops):# image_w=448, image_h=448):
    index = 0
    sum_dice = 0
    sum_iou = 0
    sum_vc8 = 0
    sum_vc16 = 0
    for poly_true, poly_pred, crop in zip(y_true[0:],y_pred[0:], crops[0:]):
        #print ('--'+str(index)+'--')
        # print ()
        

        if len(poly_true) !=0:
            if len(poly_pred) !=0: 
                #polygon
                if (True):
                    try:
                        image_w = crop[2]-crop[0]
                        image_h = crop[3]-crop[1]
                    except:
                        # print ("index: ", index)
                        # print (crop)
                        image_w =0
                        image_h = 0
                        #print (poly_true)
                        empty_true=False
                        empty_pred=False
                        try:
                            max_value_t = max(max(max(sublist) for sublist in poly_true))
                        except:
                            empty_true=True
                        try:
                            max_value_p = max(max(max(sublist) for sublist in poly_pred))
                        except:
                            empty_pred = True

                        
                        # if empty_pred and empty_true:
                        #     do_cal = True
                        
                        max_v = max([max_value_t, max_value_p])
                        if max_v > image_w:
                                image_w = max_v
                                image_h = max_v
                    
                    try:
                        masks = [polygon_to_mask(polygon[0],image_w,image_h) for polygon in poly_true]
                        results = [polygon_to_mask(polygon[0],image_w,image_h) for polygon in poly_pred]
                        dice, iou, vc8, vc16 = calculate_merged(results, masks)
                    except:
                        #print ('erroe')
                        # print ('index',index)
                        dice = 0
                        iou = 0
                        vc8=0
                        vc16 = 0
                #mask
                else:
                    masks = [load_mask_from_path(polygon[0]) for polygon in poly_true]
                    results = [load_mask_from_path(polygon[0]) for polygon in poly_pred]
                    # load json code
                    # masks = 
                    # results = 
                    dice, iou, vc8, vc16 = calculate_merged(results, masks)
                
            else:
                dice = 0
                iou = 0
                vc8=0
                vc16 = 0

        else:
            if len(poly_pred)!=0:
                dice = 0
                iou = 0
                vc8=0
                vc16 = 0
            else:
                dice = 1
                iou = 1
                vc8=1
                vc16 = 1
        sum_dice = sum_dice+dice
        sum_iou = sum_iou+iou
        sum_vc8 = sum_vc8+vc8
        sum_vc16 = sum_vc16+vc16
        index = index+1
    m_dice = (sum_dice/len(y_true))*100
    m_iou = (sum_iou/len(y_true))*100
    m_vc8 = (sum_vc8/len(y_true))*100
    m_vc16 = (sum_vc16/len(y_true))*100
    return m_dice, m_iou, m_vc8, m_vc16

def evaluation_segmentation_single_json(y_true, y_pred, crops):# image_w=448, image_h=448):
    index = 0
    sum_dice = 0
    sum_iou = 0
    sum_vc8 = 0
    sum_vc16 = 0
    for poly_true, poly_pred, crop in zip(y_true[0:],y_pred[0:], crops[0:]):
        #print ('--'+str(index)+'--')
        # print ()
        

        if len(poly_true) !=0:
            if len(poly_pred) !=0: 
                #polygon
                if (True):
                    try:
                        image_w = crop[2]-crop[0]
                        image_h = crop[3]-crop[1]
                    except:
                        # print ("index: ", index)
                        # print (crop)
                        image_w =0
                        image_h = 0
                        #print (poly_true)
                        empty_true=False
                        empty_pred=False
                        try:
                            max_value_t = max(max(max(sublist) for sublist in poly_true))
                        except:
                            empty_true=True
                        try:
                            max_value_p = max(max(max(sublist) for sublist in poly_pred))
                        except:
                            empty_pred = True

                        
                        # if empty_pred and empty_true:
                        #     do_cal = True
                        
                        max_v = max([max_value_t, max_value_p])
                        if max_v > image_w:
                                image_w = max_v
                                image_h = max_v
                    
                    try:
                        masks = [polygon_to_mask(polygon[0],image_w,image_h) for polygon in poly_true]
                        results = [polygon_to_mask(polygon[0],image_w,image_h) for polygon in poly_pred]
                        dice, iou, vc8, vc16 = calculate_merged(results, masks)
                    except:
                        #print ('erroe')
                        # print ('index',index)
                        dice = 0
                        iou = 0
                        vc8=0
                        vc16 = 0
                #mask
                else:
                    masks = [load_mask_from_path(polygon[0]) for polygon in poly_true]
                    results = [load_mask_from_path(polygon[0]) for polygon in poly_pred]
                    # load json code
                    # masks = 
                    # results = 
                    dice, iou, vc8, vc16 = calculate_merged(results, masks)
                
            else:
                dice = 0
                iou = 0
                vc8=0
                vc16 = 0

        else:
            if len(poly_pred)!=0:
                dice = 0
                iou = 0
                vc8=0
                vc16 = 0
            else:
                dice = 1
                iou = 1
                vc8=1
                vc16 = 1
        sum_dice = sum_dice+dice
        sum_iou = sum_iou+iou
        sum_vc8 = sum_vc8+vc8
        sum_vc16 = sum_vc16+vc16
        index = index+1
    m_dice = (sum_dice/len(y_true))*100
    m_iou = (sum_iou/len(y_true))*100
    m_vc8 = (sum_vc8/len(y_true))*100
    m_vc16 = (sum_vc16/len(y_true))*100
    return m_dice, m_iou, m_vc8, m_vc16