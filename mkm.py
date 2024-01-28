#!/usr/bin/env python3
'''
@作者: 风沐白
@文件: mkm.py
@描述: 快速打包 Magsik 字体模块
@版本: v2.3.1
'''

import os
import sys
import shutil
import time
import getopt
from getopt import GetoptError
import atexit
import json
from py7zr import pack_7zarchive, unpack_7zarchive
from fontTools.ttLib import TTFont, TTLibError

Full = False
FontName = None
Version = None
Prop = None
FontHomeDir = 'fonts_tmp'
VersionCode = time.strftime("%Y%m%d", time.localtime())
Weight = {100: 1,
         200: 2,
         300: 3,
         400: 4,
         500: 5,
         600: 6,
         700: 7,
         800: 8,
         900: 9}


shutil.register_archive_format('7zip',
                               pack_7zarchive,
                               description='7zip archive')
shutil.register_unpack_format('7zip',
                              ['.7z'],
                              unpack_7zarchive,
                              description='7zip archive')


class FontFamily():
    def __init__(self, font: TTFont, name: str) -> None:
        self.name = name
        for n in font['name'].names:
            s = n.toStr()
            if n.nameID == 5 and s.isascii():
                self.version = s
        self.files = set()
        pass


class ModuleProp():
    def __init__(self, id,
                 name,
                 version,
                 versionCode,
                 author,
                 description,
                 minMagisk) -> None:
        self.id = id
        self.name = name
        self.version = version
        self.versionCode = versionCode
        self.author = author
        self.description = description
        self.minMagisk = minMagisk
        pass

    def write(self):
        if os.path.exists('outs/module.prop'):
            with open('outs/module.prop', 'w') as f:
                lines = []
                lines.append('id={}\n'.format(self.id))
                lines.append('name={}\n'.format(self.name))
                lines.append('version={}\n'.format(self.version))
                lines.append('versionCode={}\n'.format(self.versionCode))
                lines.append('minMagisk={}\n'.format(self.minMagisk))
                lines.append('author={}\n'.format(self.author))
                lines.append('description={}\n'.format(self.description))
                lines.append(
                    'updateJson=https://raw.githubusercontent.com/entr0pia/font-modular/master/update.json\n')
                f.writelines(lines)
        else:
            print('模板文件可能已损坏')
            exit()
        return


def help():
    print('Usage:\n',
          'python [-s] mkm.py path_to_ttf_font(s)\n')
    return


def get_font_family():
    '''获取字体家族'''
    # {Font_Family_name: class FontFamily}
    font_families = dict()
    for font_file_name in os.listdir(FontHomeDir):
        file_path = '{}/{}'.format(FontHomeDir, font_file_name)
        try:
            font = TTFont(file_path)
        except TTLibError as e:
            print(e)
            exit()
        except PermissionError as e:
            print(e)
            exit()
        name1 = ''
        has_name16 = False
        for n in font['name'].names:
            name = n.toStr()
            if name.isascii():
                if n.nameID == 16:
                    has_name16 = True
                    if name not in font_families.keys():
                        font_families[name] = FontFamily(font, name)
                    font_families[name].files.add(file_path)
                    break
                if n.nameID == 1:
                    name1 = name
        if not has_name16:
            name = name1
            if name not in font_families.keys():
                font_families[name] = FontFamily(font, name)
            font_families[name].files.add(file_path)

    return font_families


def extra_fonts(filename: str):
    '''提取字体模块'''
    print('from {} extra fonts ...'.format(filename))
    if os.path.isdir(filename) and os.listdir(filename) != []:
        global FontHomeDir
        FontHomeDir = filename
        return
    try:
        shutil.unpack_archive(filename, FontHomeDir)
    except Exception as e:
        print(e)
        print('解压失败, 请手动解压')
        exit()
    return


def select_font(font_families: dict, family_name: str):
    '''筛选字体'''
    global FontName, Version, Prop
    # {file_path: Weight}
    has_regular = False
    selected = dict()
    files = []
    if family_name != None:
        files = font_families[family_name].files
        FontName = family_name
        Version = font_families[family_name].version
    else:
        for f in font_families.values():
            files.extend(list(f.files))
    for i in files:
        font = TTFont(i)
        # 跳过斜体
        if font['OS/2'].fsSelection & 1 == 1:
            continue
        weight = font['OS/2'].usWeightClass
        # 跳过不兼容的字重
        if weight not in Weight.keys():
            continue
        selected[i] = Weight[weight]
        if selected[i] == 4:
            has_regular = True
            if family_name == None:
                for n in font['name'].names:
                    name = n.toStr()
                    if name.isascii():
                        if n.nameID == 1:
                            FontName = name
                        if n.nameID == 5:
                            Version = name

    if not has_regular:
        print('缺少常规 (Normal, Regular) 字体')
        exit()

    Prop = ModuleProp(FontName.replace(' ', '-').lower(),
                      FontName,
                      Version,
                      VersionCode,
                      'entr0pia, lxgw @ Github',
                      '{} with {} Weight(s)'.format(FontName, len(selected)),
                      20400)
    return selected


def zip_font_module(selected_dict: dict):
    '''打包字体模块'''
    print('packing font module ...')
    fontfiles = selected_dict.keys()
    if os.path.exists('outs'):
        shutil.rmtree('outs')
    shutil.copytree('template', 'outs')
    Prop.write()
    for f in fontfiles:
        shutil.copy2(f,
                     'outs/system/fonts/fontw{}.ttf'.format(selected_dict[f]))
    zip_name = '{}_{}'.format(FontName, Version).replace(' ', '_')
    shutil.make_archive(zip_name,
                        'zip',
                        'outs')
    update_json(zip_name)


@atexit.register
def clean():
    '''清理工作区'''
    if os.path.exists('fonts_tmp'):
        shutil.rmtree('fonts_tmp')
    if os.path.exists('outs'):
        shutil.rmtree('outs')


def input_select(font_families: dict):
    key_dict = dict()
    print('发现字体:')
    for i, e in enumerate(font_families.keys()):
        key_dict[i] = e
        print('{}:\t{}'.format(i, font_families[e].name))
    print('选择字体 (输入序号): ', end='')
    i = input()
    return key_dict[int(i)]


def update_json(zip_name):
    with open('update.json','w') as f:
        json.dump({"version": Version,
                   "versionCode": VersionCode,
                   "zipUrl": f'https://github.com/entr0pia/font-modular/releases/latest/download/{zip_name}.zip',
                   "changelog": "https://raw.githubusercontent.com/entr0pia/font-modular/master/change.log"},
                   f,
                   indent=4)
    return


if __name__ == '__main__':
    if (l := len(sys.argv)) < 2:
        print('未指定字体文件')
        help()
        exit()

    if sys.argv[1] in ['?', '/?', '-h', '--help']:
        help()
        exit()
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 's')
    except GetoptError as e:
        print(e)
        help()
        exit()

    for op in optlist:
        if op[0] == '-s':
            Full = False

    extra_fonts(args[0])
    if not os.path.exists(FontHomeDir) or os.listdir(FontHomeDir) == []:
        print('未解压出字体文件')
        exit()

    font_families = get_font_family()
    selected_dict = dict()
    if not Full:
        selected_dict = select_font(font_families, input_select(font_families))
    else:
        selected_dict = select_font(font_families, None)
    zip_font_module(selected_dict)
    print('打包成功, 正在清理...')
