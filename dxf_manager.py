import ezdxf
import re
import os
from ezdxf import units
from typing import List


output_directory = os.path.join('game', 'output')

def add_rounded_rectangle(msp, x, y, width, height, radius):
    #y=y-height #corner alignment
    # Define corner centers
    bl = (x + radius, y + radius)  # Bottom-left
    br = (x + width - radius, y + radius)  # Bottom-right
    tr = (x + width - radius, y + height - radius)  # Top-right
    tl = (x + radius, y + height - radius)  # Top-left

    # Lines between arcs
    msp.add_line((bl[0], y), (br[0], y))  # Bottom edge
    msp.add_line((x + width, br[1]), (x + width, tr[1]))  # Right edge
    msp.add_line((tr[0], y + height), (tl[0], y + height))  # Top edge
    msp.add_line((x, tl[1]), (x, bl[1]))  # Left edge

    # Corner arcs (always counter-clockwise in DXF)
    msp.add_arc(center=br, radius=radius, start_angle=270, end_angle=360)  # Bottom-right
    msp.add_arc(center=tr, radius=radius, start_angle=0, end_angle=90)     # Top-right
    msp.add_arc(center=tl, radius=radius, start_angle=90, end_angle=180)   # Top-left
    msp.add_arc(center=bl, radius=radius, start_angle=180, end_angle=270)  # Bottom-left



# Create new DXF document
def generate_dxf(card_width: str, card_height: str, card_radius: str, x_pos: List[int], y_pos: List[int], ppi:int, filename:str):
    doc = ezdxf.new(dxfversion='R2010')
    
    float_pattern = r"(?:\d+\.\d*|\.\d+|\d+)"  # matches 1.0, .5, or 2
    # Match mm
    mm_width = re.fullmatch(rf"({float_pattern})mm", card_width)
    mm_height = re.fullmatch(rf"({float_pattern})mm", card_height)
    mm_radius = re.fullmatch(rf"({float_pattern})mm", card_radius)
    if mm_width and mm_height and mm_radius:
        doc.units = units.MM
        width = float(mm_width.group(1))
        height = float(mm_height.group(1))
        radius = float(mm_radius.group(1))

    # Match inches
    in_width = re.fullmatch(rf"({float_pattern})in", card_width)
    in_height = re.fullmatch(rf"({float_pattern})in", card_width)
    in_radius = re.fullmatch(rf"({float_pattern})mm", card_radius)
    if in_width and in_height and in_radius:
        doc.units = units.IN
        width = float(in_width.group(1))
        height = float(in_height.group(1))
        radius = float(in_radius.group(1))
    
    
    msp = doc.modelspace()
    
    
    for x in range(len(x_pos)):
        for y in range(len(y_pos)):
            if doc.units == units.IN:
                pos_x = x_pos[x] / ppi
                pos_y = y_pos[y] / ppi
            else:
                pos_x = x_pos[x] * 25.4 / ppi
                pos_y = y_pos[y] * 25.4 / ppi
            add_rounded_rectangle(msp, pos_x, pos_y, width, height, radius)
        

    # Save DXF
    default_output_path = os.path.join(output_directory, f'{filename}.dxf')
    doc.saveas(default_output_path)
    print("DXF file 'template.dxf' created.")