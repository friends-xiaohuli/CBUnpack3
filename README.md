# CBUNPAK 3.0

尘白禁区 的快速解包方案

仅限国服，国际服秘钥不同

config.json 自己得看着改配置文件，具体配置往下翻README

另外**首次运行自动生成 手动修改后 程序将自动热重载**，但是要记得保存文件才能被读取到

## License

```text
GNU General Public License Version 3

Copyright (C) 2025  friends-xiaohuli

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

## Config.json 设置说明

### 工具 设置路径

```text
"ffm_path": ffmpeg.exe 文件路径
"umo_path": umodel.exe 文件路径
"vgm_path": vgmstream-cli.exe 文件路径
"quickbms_path": quickbms_4gb_files.exe 文件路径
"spine_path": Spine.exe 文件路径
"max_workers": 多线程数
"UseCNName": 音频文件应用匹配到的中文名
```

### 解密解包 设置路径

```text
"pak_path": snow_pak 文件夹路径(必填，参考路径".\Snow\data\game\Game\Content\Paks")
"unpack_path": INPUT路径 解密完成，待提取资源 文件夹路径(可选，默认为 "./unpack")
"resource_path": OUT路径 提取资源导出 文件夹路径(可选，默认为 "./unpack")
```

### 提取增量资源 设置路径

```text
"past_path": 旧版本 解包文件夹路径
"new_path": 新版本 解包文件夹路径
"increase_path": 增量解包导出 文件夹路径(可选，默认为 "./increase")
```
