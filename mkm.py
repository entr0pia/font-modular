#!/usr/bin/env python3
'''
@作者: 风沐白
@文件: mkm.py
@描述: 快速打包 Magsik 字体模块
@版本: v2.0.1
'''

import os
import sys
import shutil
import time
import atexit
from py7zr import pack_7zarchive, unpack_7zarchive
from fontTools.ttLib import TTFont, TTLibError


FontName = None
Version = None
Prop = None
FontHomeDir = 'fonts'
VersionCode = time.strftime("%y%m%d", time.localtime())
Width = {100: 1,
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
    def __init__(self, font: TTFont) -> None:
        self.name = []
        for n in font['name'].names:
            s = n.toStr()
            if n.nameID == 16:
                self.name.append(s)
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
                lines.append('description={}'.format(self.description))
                f.writelines(lines)
        else:
            print('模板文件可能已损坏')
            exit()
        return


def help():
    print('Usage:\n',
          'python mkm.py path_to_ttf_font(s)\n')
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
        for n in font['name'].names:
            name = n.toStr()
            if n.nameID == 16 and name.isascii():
                if name not in font_families.keys():
                    font_families[name] = FontFamily(font)
                font_families[name].files.add(file_path)
    return font_families


def extra_fonts(filename: str):
    '''提取字体模块'''
    print('from {} extra fonts ...'.format(filename))
    if os.path.isdir(filename) and os.listdir(filename) != []:
        global FontHomeDir
        FontHomeDir = filename
        return
    shutil.unpack_archive(filename, FontHomeDir)
    return


def select_font(font_families: dict, family_name: str):
    '''筛选字体'''
    global FontName, Version, Prop
    FontName = family_name
    Version = font_families[family_name].version
    # {file_path: width}
    selected = dict()
    for i in font_families[family_name].files:
        font = TTFont(i)
        # 跳过斜体
        if font['OS/2'].fsSelection & 1 == 1:
            continue
        selected[i] = Width[font['OS/2'].usWeightClass]

    Prop = ModuleProp(family_name.replace(' ', '-').lower(),
                      FontName,
                      Version,
                      VersionCode,
                      '落霞孤鹜 [lxgwshare], entr0pia@Github',
                      '{} with {} Weight(s)'.format(FontName, len(selected)),
                      19000)
    return selected


def zip_font_module(selected_dict: dict):
    '''打包字体模块'''
    print('packing font module ...')
    fontfiles = selected_dict.keys()
    has_regular = 4 in selected_dict.values()
    if not has_regular:
        print('所选字体: {}'.format(fontfiles))
        print('缺少常规 (Normal, Regular) 字体')
        exit()
    if os.path.exists('outs'):
        shutil.rmtree('outs')
    shutil.copytree('template', 'outs')
    Prop.write()
    for f in fontfiles:
        shutil.copy2(f,
                     'outs/system/fonts/fontw{}.ttf'.format(selected_dict[f]))
    shutil.make_archive('{} {}'.format(FontName, Version),
                        'zip',
                        'outs')

@atexit.register
def clean():
    '''清理工作区'''
    if os.path.exists('fonts'):
        shutil.rmtree('fonts')
    if os.path.exists('outs'):
        shutil.rmtree('outs')


def input_select(font_families: dict):
    key_dict = dict()
    print('发现字体:')
    for i, e in enumerate(font_families.keys()):
        key_dict[i] = e
        print('{}:\t{}'.format(i, ', '.join(font_families[e].name)))
    print('选择字体 (输入序号): ', end='')
    i = input()
    return key_dict[int(i)]


if __name__ == '__main__':
    if (l := len(sys.argv)) < 2:
        print('未指定字体文件')
        help()
        exit()

    if sys.argv[1] in ['?', '/?', '-h', '--help']:
        help()
        exit()

    extra_fonts(sys.argv[1])
    if not os.path.exists(FontHomeDir) or os.listdir(FontHomeDir) == []:
        print('未解压出字体文件')
        exit()

    font_families = get_font_family()
    selected_dict = select_font(font_families, input_select(font_families))
    zip_font_module(selected_dict)