# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image

def change_pic(path_pic):
    im = Image.open(path_pic)
    im = im.convert('RGBA')
    data = np.array(im)
    rgb = data[:,:,:3]
    color = [242, 242, 242]
    white = [255,255,255,255]
    mask = np.all(rgb == color, axis=-1)
    data[mask] = white
    new_im = Image.fromarray(data)
    print(path_pic)
    new_im.save(path_pic)