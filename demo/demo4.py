import json
import os


def write_json(directory):
    for root, dirs, files in os.walk(directory):
        # print(f"当前目录: {root, dirs, files}")
        for file in files:
            ba, suf = os.path.splitext(file)
            if suf == ".json":
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    _dir = json.load(f)
                    _dir["skeleton"]["images"] = 'images'
                    # print(_dir)
                    # return 0
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(_dir, f)
                print(f"Complete：{filepath}")


# json文件修改图集识别位置
if __name__ == '__main__':
    write_json(r'E:\Unpack\assets\23_spine\dressspine')
