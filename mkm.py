#!/usr/bin/env python3
'''
@作者: 风沐白
@文件: mkm.py
@描述: 由更纱黑体制作 magsik 字体模块
'''

import os
import sys
import shutil
import py7zr
import re


FontName = 'sarasa-mono-sc'
Version = 'v2.003'
VersionCode = 32
Width = {'thin': 1,
         'extralight': 2,
         'light': 3,
         'regular': 4,
         'medium': 5,
         'semibold': 6,
         'bold': 7,
         'extrabold': 8,
         'heavy': 9}


def help():
    print('Usage:\n',
          'python mkm.py fonts.zip\n')
    return


def extra_fonts(filename: str, fontname: str):
    '''提取字体模块'''
    print('from {} extra {} fonts ...'.format(filename, fontname))
    with py7zr.SevenZipFile(filename, 'r') as z:
        allfiles = z.getnames()
        filter_pattern = re.compile('{}.*'.format(fontname))
        selected = [f for f in allfiles if 'italic' not in f and
                    filter_pattern.match(f)]
        if not os.path.exists('fonts'):
            os.mkdir('fonts')
        z.extract('fonts', selected)
    return


def zip_font_module():
    '''打包字体模块'''
    print('packing font module ...')
    if os.path.exists('outs'):
        shutil.rmtree('outs')
    shutil.copytree('template', 'outs')
    fontfiles = os.listdir('fonts')
    for f in fontfiles:
        for w in Width.keys():
            if w in f:
                shutil.copy2('fonts/{}'.format(f),
                             'outs/system/fonts/fontw{}.ttf'.format(Width[w]))
    shutil.make_archive('{}-unhinted-{} ({})'.format(FontName, Version, VersionCode),
                        'zip',
                        'outs')


def clean():
    '''清理工作区'''
    if os.path.exists('fonts'):
        shutil.rmtree('fonts')
    if os.path.exists('outs'):
        shutil.rmtree('outs')


if __name__ == '__main__':
    if (l := len(sys.argv)) < 2:
        print('未指定字体文件')
        help()
        exit()

    extra_fonts(sys.argv[1], FontName)
    if not os.path.exists('fonts') or os.listdir('fonts') == []:
        print('未解压出字体文件')
        exit()

    zip_font_module()
    clean()
