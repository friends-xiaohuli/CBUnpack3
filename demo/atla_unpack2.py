# -*- coding: utf-8 -*-
import os
import os.path
import shutil
import json
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm


def premultiply_alpha(image):
    '''
    若输出的贴图文件应用了预乘alpha
    :param image:
    :return:
    '''
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    for i in range(image.width):
        for j in range(image.height):
            red, green, blue, alpha = image.getpixel((i, j))
            if alpha > 0:
                image.putpixel((i, j),
                               tuple([min(max(int(p / alpha * 255), 0), 255) for p in (red, green, blue)] + [alpha]))
    return image


def split_atlas(fileName, output_path: str = None, atlas_path: str = None):
    '''
    :param fileName: 文件名
    :param output_path: 输出目录
    :param atlas_path: 图集.atlas文件
    :return:
    '''
    print(atlas_path)
    if output_path is None:
        output_path = os.path.join(os.getcwd(), fileName)
    if atlas_path is None:
        atlas_path = fileName + '.atlas'
    with open(atlas_path, 'r', encoding='utf-8-sig') as atlas:
        os.makedirs(output_path, exist_ok=True)
        # print(atlas.readlines())
        while True:
            _line = atlas.readline()
            if not _line:
                continue
            elif ".png" in _line:
                png_name = _line.strip("\n")
                png_path = os.path.join(os.path.split(atlas_path)[0], png_name)
                if not os.path.exists(png_path):
                    print(png_path)
                    png_path = os.path.join(os.path.split(atlas_path)[0], "Textures", png_name)
                    if not os.path.exists(png_path):
                        print(png_path)
                        raise ValueError
                ori_image = Image.open(png_path)

                big_image_size = atlas.readline()
                big_image_width, big_image_height = list(map(int, big_image_size.split(":")[1].split(",")))
                big_image = ori_image.resize((big_image_width, big_image_height))

                atlas.readline()
                atlas.readline()
                atlas.readline()

                png_name = None
                rotate_angle = 0
                offset_x, offset_y = 0, 0
                while True:
                    line1 = atlas.readline()  # name
                    print(line1)
                    if not line1:
                        break
                    if "bounds" in line1:
                        ltx, lty, width, height = list(map(int, line1.split(":")[1].strip("\n").split(",")))
                        origx, origy = width, height
                    elif "rotate" in line1:
                        if "false" in line1:
                            rotate_angle = 0
                        elif "true" in line1:
                            rotate_angle = 90
                        else:
                            rotate_angle = int(line1.split(":")[1].strip("\n"))
                    elif "offsets" in line1:
                        offset_x1, offset_y1, offset_x, offset_y = list(map(int, line1.strip("\n").split(":")[1].split(",")))
                    else:
                        if png_name:
                            if rotate_angle == 0 or rotate_angle == 180:
                                rbx = ltx + width
                                rby = lty + height
                            elif rotate_angle == 90:
                                rbx = ltx + height
                                rby = lty + width
                            elif rotate_angle == 270:
                                rbx = ltx + height
                                rby = lty + width
                            # print(name, width, height, ltx, lty, rbx, rby)
                            result_image = Image.new("RGBA", (origx, origy))
                            rect_on_big = big_image.crop((ltx, lty, rbx, rby))
                            if rotate_angle:
                                rect_on_big = rect_on_big.rotate(-rotate_angle, expand=True)
                            # if premultiply:
                            #     rect_on_big = premultiply_alpha(rect_on_big)
                            result_image.paste(rect_on_big, (offset_x, origy - height - offset_y))
                            result_image.save(output_path + '/' + png_name+".png")
                            png_name = None
                        else:
                            png_name = line1.strip("\n")
                            rotate_angle = 0
                            offset_x, offset_y = 0, 0


if __name__ == '__main__':
    input_path = filedialog.askdirectory(title="选择需要批量解包的目录")
    # for root, dirs, files in os.walk(input_path):
    #     for filename in files:
    #         if filename.endswith(".png"):
    #             if os.path.split(root)[1] == "Textures":
    #                 old_path = os.path.join(root, filename)
    #                 newpath = os.path.join(os.path.split(root)[0], filename)
    #                 # print(old_path, newpath)
    #                 shutil.copy(old_path, newpath)
    #                 os.remove(old_path)
    for root, dirs, files in os.walk(input_path):
        for filename in files:
            if filename.endswith(".atlas"):
                atlas_path = os.path.join(root, filename)
                unitName = os.path.split(filename)[1]
                outputPath = os.path.join(root, 'images')
                if not os.path.exists(outputPath):
                    os.makedirs(outputPath)
                split_atlas(unitName, output_path=outputPath, atlas_path=atlas_path)

    # for file in pbar:
    #     pbar.set_description(f"Solving {file} ...")
    #     if os.path.isdir(os.path.join(input_path, file)):
    #         unitName = os.path.split(file)[1]
    #         outputPath = os.path.join(input_path, file)
    #         split_atlas(unitName, output_path=outputPath, atlas_path=os.path.join(outputPath, unitName + '.atlas'))