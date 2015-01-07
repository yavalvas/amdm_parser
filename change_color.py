# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
#import os
#script_dir = os.path.dirname(os.path.abspath(__file__))
def change_pic(path_pic):
    im = Image.open(path_pic)
    im = im.convert('RGBA')
    data = np.array(im)
    # just use the rgb values for comparison
    rgb = data[:,:,:3]
    color = [242, 242, 242]   # Original value
    black = [0,0,0, 255]
    white = [255,255,255,255]
    mask = np.all(rgb == color, axis = -1)
    # change all pixels that match color to white
    data[mask] = white
    # change all pixels that don't match color to black
    ##data[np.logical_not(mask)] = black
    new_im = Image.fromarray(data)
    print path_pic
    # orig_color = (242,242,242)
    new_im.save(path_pic)