import json
import math
import os
import re
from types import SimpleNamespace
from xml.dom import ValidationErr
from dxf_manager import generate_dxf

# Specify directory locations
sizing_path = os.path.join('assets', 'sizing.json')


def generate_layout(
    card_size: str,
    paper_size: str,
    orientation: bool, #true=horizontal / false:vertical
):
    with open(sizing_path, 'r') as sizing_file:
        try:
            sizing = json.load(sizing_file, object_hook=lambda d: SimpleNamespace(**d))

        except ValidationErr as e:
            raise Exception(f'Cannot parse sizing.json: {e}.')
        
        # paper_layout represents the size of a paper and all possible card layouts
        if not hasattr(sizing.paper_sizes, paper_size):
            raise Exception(f'Unsupported paper size "{paper_size}". Try paper sizes: {sizing.paper_sizes.keys()}.')

        # card_layout_size represents the size of a card
        if not hasattr(sizing.card_sizes, card_size):
            raise Exception(f'Unsupported card size "{card_size}". Try card sizes: {sizing.card_sizes.keys()}.')

    return generate_custom_layout( getattr(sizing.card_sizes, card_size).width, 
                            getattr(sizing.card_sizes, card_size).height, 
                            getattr(sizing.card_sizes, card_size).radius, 
                            getattr(sizing.paper_sizes, paper_size).width,
                            getattr(sizing.paper_sizes, paper_size).height,
                            orientation,
                            sizing.ppi,
                            card_size,
                            paper_size)


def generate_custom_layout(
    card_width: str,
    card_height: str,
    card_radius: str,
    page_width: str,
    page_height: str,
    orientation: bool, #true=horizontal / false:vertical
    ppi: int,
    card_size: str,
    paper_size: str,
):
    #maximum bleed of 1mm and space to registration marks of 2mm
    bleed_x_px = size_to_pixel("1mm", ppi)
    bleed_y_px = bleed_x_px
    space_x_px = size_to_pixel("2mm", ppi)
    space_y_px = space_x_px
    
    #Page size to pixels
    page_width_px = size_to_pixel(page_width, ppi)
    page_height_px = size_to_pixel(page_height, ppi)
    
    #10mm min inset + 5mm length of silhouette at 300ppi
    min_margin = size_to_pixel("10mm", ppi)
    margin_x = size_to_pixel("15mm", ppi)
    margin_y = margin_x
    
    if orientation:
        card_width_px = size_to_pixel(card_height, ppi)
        card_height_px = size_to_pixel(card_width, ppi)
    else:
        card_width_px = size_to_pixel(card_width, ppi)
        card_height_px = size_to_pixel(card_height, ppi)
    
    available_width = page_width_px - (2 * (margin_x))
    available_height = page_height_px - (2 * (margin_y))
    
    min_available_width = page_width_px - (2 * min_margin)
    min_available_height = page_height_px - (2 * min_margin)
    
    #calculate num rows/cols
    num_rows = math.floor((available_height) / (card_height_px))
    num_cols = math.floor((available_width) / (card_width_px))
    
    #Validate is space available outside main margins
    max_num_rows = math.floor((min_available_height) / (card_height_px))
    max_num_cols = math.floor((min_available_width) / (card_width_px))
    
    #Validate which margin to expand
    if num_rows<max_num_rows and num_cols<max_num_cols:
        #Expand side with biggest spare room (best bleed)
        filled_height = card_height_px * num_rows + (2 * space_y_px) + (bleed_y_px * (num_rows - 1))
        filled_width = card_width_px * num_cols + (2 * space_x_px) + (bleed_x_px * (num_cols - 1))
        if (filled_height - available_height) > (filled_width - available_width):
            num_rows=max_num_rows
            margin_y=min_margin
            space_y_px = 0
            available_height = min_available_height
        else:
            num_cols=max_num_cols
            margin_x=min_margin
            space_x_px = 0
            available_width = min_available_width
    elif num_rows<max_num_rows and num_cols==max_num_cols:
        num_rows=max_num_rows
        margin_y=min_margin
        space_y_px = 0
        available_height = min_available_height
    elif num_rows==max_num_rows and num_cols<max_num_cols:
        num_cols=max_num_cols
        margin_x=min_margin
        space_x_px = 0
        available_width = min_available_width
        
    #Calculate max bleed and min space to registration marks
    filled_height = card_height_px * num_rows + (2 * space_y_px) + (bleed_y_px * (num_rows - 1))
    filled_width = card_width_px * num_cols + (2 * space_x_px) + (bleed_x_px * (num_cols - 1))

    while available_height < filled_height:
        if bleed_y_px == 0:
            space_y_px = space_y_px - 1 
        else:
            bleed_y_px = bleed_y_px - 1
        filled_height = card_height_px * num_rows + (2 * space_y_px) + (bleed_y_px * (num_rows - 1))

    while available_width < filled_width:
        if bleed_x_px == 0:
            space_x_px = space_x_px - 1 
        else:
            bleed_x_px = bleed_x_px - 1
        filled_width = card_width_px * num_cols + (2 * space_x_px) + (bleed_x_px * (num_cols - 1))


    start_x = math.floor(margin_x + space_x_px + ((available_width - filled_width) / 2))
    start_y = math.floor(margin_y + space_y_px + ((available_height - filled_height) / 2))
    
    x_pos=[start_x]
    y_pos=[start_y]
        
    for x in range(1, num_cols):  # fill remanining values
        x_pos.append(start_x + (x * (card_width_px + bleed_x_px)))
    
    for y in range(1, num_rows):  # fill remanining values
        y_pos.append(start_y + (y * (card_height_px + bleed_y_px)))
    
    #Generate template
    if orientation:
        generate_dxf(card_height, card_width, card_radius, x_pos, y_pos, ppi, f"self_generated_{paper_size}_{card_size}")
    else:
        generate_dxf(card_width, card_height, card_radius, x_pos, y_pos, ppi, f"self_generated_{paper_size}_{card_size}")
    
        
    card_sizes={}
    card_sizes[card_size] = {
                                "width": card_width_px,
                                "height": card_height_px
                            }
    
    card_layouts={}
    card_layouts[card_size] = {
                                "x_pos": x_pos,
                                "y_pos": y_pos,
                                "template": f"self_generated_{paper_size}_{card_size}"
                            }
    paper_layouts={}
    paper_layouts[paper_size] = {
                                "width":page_width_px,
                                "height":page_height_px,
                                "card_layouts":card_layouts
                            }
    return {
        "card_sizes": card_sizes,
        "paper_layouts": paper_layouts
    }
    
    
def size_to_pixel(size_string, ppi):    
    float_pattern = r"(?:\d+\.\d*|\.\d+|\d+)"  # matches 1.0, .5, or 2
    
    # Match mm
    mm_match = re.fullmatch(rf"({float_pattern})mm", size_string)
    if mm_match:
        size_mm = float(mm_match.group(1))
        return math.floor(size_mm / 25.4 * ppi)

    # Match inches
    in_match = re.fullmatch(rf"({float_pattern})in", size_string)
    if in_match:
        size_in = float(in_match.group(1))
        return math.floor(size_in*ppi)
    
    #If no match
    return math.floor(float(size_string))
