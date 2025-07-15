import os
from tkinter import filedialog


# 灵魂潮汐包体解密
def soul_tide_decode(_directory):
    _list = os.walk(directory)
    tn = len(list(_list))
    _list = os.walk(directory)
    tnum = 0
    for root, dirs, files in _list:
        tnum += 1
        fn = len(files)
        fnum = 0
        _str = f"进度 {tnum}/{tn} | "
        for file in files:
            fnum += 1
            ba, suf = os.path.splitext(file)
            if suf == ".ab":  # ".ab"
                _filepath = os.path.join(root, file)
                with open(_filepath, 'rb') as f:  # 以二进制模式打开文件
                    file_content = f.read()  # 读取整个文件内容
                if file_content[:6] == b'iqigam':  #
                    modified_content = file_content[6:]
                else:
                    continue
                # 将修改后的内容写入新文件
                with open(_filepath, 'wb') as output_file:  # 以二进制模式写入新文件
                    output_file.write(modified_content)
                print(_str + f"{fnum}/{fn} : " + _filepath)


# 深空之眼解密
def skzy_decode(_directory):
    _list = os.walk(directory)
    tn = len(list(_list))
    _list = os.walk(directory)
    tnum = 0
    for root, dirs, files in _list:
        tnum += 1
        fn = len(files)
        fnum = 0
        _str = f"进度 {tnum}/{tn} | "
        for file in files:
            fnum += 1
            ba, suf = os.path.splitext(file)
            if suf == ".ys":  # ".ab"
                _filepath = os.path.join(root, file)
                with open(_filepath, 'rb') as f:  # 以二进制模式打开文件
                    file_content = f.read()  # 读取整个文件内容
                seg = file_content[:50]
                if b"UnityFS" in seg:
                    _num = seg.find(b"UnityFS")
                    if not _num:
                        continue
                    modified_content = file_content[_num:]
                else:
                    continue
                # 将修改后的内容写入新文件
                with open(_filepath, 'wb') as output_file:  # 以二进制模式写入新文件
                    output_file.write(modified_content)
                print(_str + f"{fnum}/{fn} : " + _filepath)


# 环行旅舍解密
def hxls_decode(_directory):
    _list = os.walk(directory)
    tn = len(list(_list))
    _list = os.walk(directory)
    tnum = 0
    for root, dirs, files in _list:
        tnum += 1
        fn = len(files)
        fnum = 0
        _str = f"进度 {tnum}/{tn} | "
        for file in files:
            fnum += 1
            ba, suf = os.path.splitext(file)
            if suf == ".ab":  # ".ab"
                _filepath = os.path.join(root, file)
                with open(_filepath, 'rb') as f:  # 以二进制模式打开文件
                    file_content = f.read()  # 读取整个文件内容
                seg = file_content[:50]
                if b"UnityFS" in seg:
                    _num = seg.find(b"UnityFS")
                    if not _num:
                        continue
                    modified_content = file_content[_num:]
                else:
                    continue
                # 将修改后的内容写入新文件
                with open(_filepath, 'wb') as output_file:  # 以二进制模式写入新文件
                    output_file.write(modified_content)
                print(_str + f"{fnum}/{fn} : " + _filepath)


if __name__ == '__main__':
    directory = filedialog.askdirectory(title="选择需要批量解密的目录")
    # 灵魂潮汐包体解密
    # soul_tide_decode(directory)
    # 深空之眼解密
    # skzy_decode(directory)
    # 环行旅舍解密
    hxls_decode(directory)
