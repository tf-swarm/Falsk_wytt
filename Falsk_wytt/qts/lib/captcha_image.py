#!/usr/bin/env python
# -*- coding: utf-8 -*-

# refer to `https://bitbucket.org/akorn/wheezy.captcha`

import random
import string
import os.path
import os
from io import BytesIO

from PIL import Image, ImageFont, ImageDraw, ImageFilter
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from flask import make_response
from flask import app


class Bezier:
    def __init__(self):
        self.tsequence = tuple([t / 20.0 for t in range(21)])
        self.beziers = {}

    def pascal_row(self, n):
        """ Returns n-th row of Pascal's triangle
        """
        result = [1]
        x, numerator = 1, n
        for denominator in range(1, n // 2 + 1):
            x *= numerator
            x /= denominator
            result.append(x)
            numerator -= 1
        if n & 1 == 0:
            result.extend(reversed(result[:-1]))
        else:
            result.extend(reversed(result))
        return result

    def make_bezier(self, n):
        """ Bezier curves:
            http://en.wikipedia.org/wiki/B%C3%A9zier_curve#Generalization
        """
        try:
            return self.beziers[n]
        except KeyError:
            combinations = self.pascal_row(n - 1)
            result = []
            for t in self.tsequence:
                tpowers = (t ** i for i in range(n))
                upowers = ((1 - t) ** i for i in range(n - 1, -1, -1))
                coefs = [c * a * b for c, a, b in zip(combinations,
                                                      tpowers, upowers)]
                result.append(coefs)
            self.beziers[n] = result
            return result


class Captcha(object):
    def __init__(self):
        self._bezier = Bezier()
        self._dir = os.path.dirname(__file__)
        # self._captcha_path = os.path.join(self._dir, '..', 'static', 'captcha')

    @staticmethod
    def instance():
        if not hasattr(Captcha, "_instance"):
            Captcha._instance = Captcha()
        return Captcha._instance

    def initialize(self, width=200, height=75, color=None, text=None, fonts=None):
        # self.image = Image.new('RGB', (width, height), (255, 255, 255))
        print("--initialize--:", text, string.ascii_uppercase)
        # 字母和数字混合
        # self._text = text if text else random.sample(string.ascii_uppercase + string.ascii_uppercase + '3456789', 4)
        self._text = text if text else random.sample(string.digits + string.digits, 4)
        self.fonts = fonts if fonts else \
            [os.path.join(self._dir.split('lib')[0], 'utils', 'fonts',font) for font in ['Arial.ttf', 'Georgia.ttf', 'actionj.ttf']]

        self.width = width
        self.height = height
        self._color = color if color else self.random_color(0, 200, random.randint(220, 255))

    @staticmethod
    def random_color(start, end, opacity=None):
        red = random.randint(start, end)
        green = random.randint(start, end)
        blue = random.randint(start, end)
        if opacity is None:
            return red, green, blue
        return red, green, blue, opacity

    # draw image

    def background(self, image):
        Draw(image).rectangle([(0, 0), image.size], fill=self.random_color(238, 255))
        return image

    @staticmethod
    def smooth(image):
        return image.filter(ImageFilter.SMOOTH)

    def curve(self, image, width=4, number=6, color=None):
        '''
        曲线
        :param image:
        :param width:
        :param number:
        :param color:
        :return:
        '''
        dx, height = image.size
        dx /= number
        path = [(dx * i, random.randint(0, height))
                for i in range(1, number)]
        bcoefs = self._bezier.make_bezier(number - 1)
        points = []
        for coefs in bcoefs:
            points.append(tuple(sum([coef * p for coef, p in zip(coefs, ps)])
                                for ps in zip(*path)))
        Draw(image).line(points, fill=color if color else self._color, width=width)
        return image

    def noise(self, image, number=50, level=2, color=None):
        '''
        杂点
        :param image:
        :param number:
        :param level:
        :param color:
        :return:
        '''
        width, height = image.size
        dx = width / 10
        width -= dx
        dy = height / 10
        height -= dy
        draw = Draw(image)
        for i in range(number):
            x = int(random.uniform(dx, width))
            y = int(random.uniform(dy, height))
            draw.line(((x, y), (x + level, y)), fill=color if color else self._color, width=level)
        return image

    def text(self, image, fonts, font_sizes=None, drawings=None, squeeze_factor=0.75, color=None):
        color = color if color else self._color
        fonts = tuple([truetype(name, size)
                       for name in fonts
                       for size in font_sizes or (65, 70, 75)])
        draw = Draw(image)
        char_images = []
        for c in self._text:
            font = random.choice(fonts)
            c_width, c_height = draw.textsize(c, font=font)
            char_image = Image.new('RGB', (c_width, c_height), (0, 0, 0))
            char_draw = Draw(char_image)
            char_draw.text((0, 0), c, font=font, fill=color)
            char_image = char_image.crop(char_image.getbbox())
            for drawing in drawings:
                d = getattr(self, drawing)
                char_image = d(char_image)
            char_images.append(char_image)
        width, height = image.size
        offset = int((width - sum(int(i.size[0] * squeeze_factor) for i in char_images[:-1]) -char_images[-1].size[0]) / 2)
        for char_image in char_images:
            c_width, c_height = char_image.size
            mask = char_image.convert('L').point(lambda i: i * 1.97)
            image.paste(char_image, (offset, int((height - c_height) / 2)), mask)
            offset += int(c_width * squeeze_factor)
        return image

    # draw text
    @staticmethod
    def warp(image, dx_factor=0.27, dy_factor=0.21):
        width, height = image.size
        dx = width * dx_factor
        dy = height * dy_factor
        x1 = int(random.uniform(-dx, dx))
        y1 = int(random.uniform(-dy, dy))
        x2 = int(random.uniform(-dx, dx))
        y2 = int(random.uniform(-dy, dy))
        image2 = Image.new('RGB',
                           (width + abs(x1) + abs(x2),
                            height + abs(y1) + abs(y2)))
        image2.paste(image, (abs(x1), abs(y1)))
        width2, height2 = image2.size
        return image2.transform(
            (width, height), Image.QUAD,
            (x1, y1,
             -x1, height2 - y2,
             width2 + x2, height2 + y2,
             width2 - x2, -y1))

    @staticmethod
    def offset(image, dx_factor=0.1, dy_factor=0.2):
        width, height = image.size
        dx = int(random.random() * width * dx_factor)
        dy = int(random.random() * height * dy_factor)
        image2 = Image.new('RGB', (width + dx, height + dy))
        image2.paste(image, (dx, dy))
        return image2

    @staticmethod
    def rotate(image, angle=25):
        return image.rotate(
            random.uniform(-angle, angle), Image.BILINEAR, expand=1)

    def captcha(self, path=None, fmt='JPEG'):
        """Create a captcha.

        Args:
            path: save path, default None.
            fmt: image format, PNG / JPEG.
        Returns:
            A tuple, (name, text, StringIO.value).
            For example:
                ('fXZJN4AFxHGoU5mIlcsdOypa', 'JGW9', '\x89PNG\r\n\x1a\n\x00\x00\x00\r...')

        """
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        image = self.background(image)
        image = self.text(image, self.fonts, drawings=['warp', 'rotate', 'offset'])
        image = self.curve(image)
        image = self.noise(image)
        image = self.smooth(image)
        name = "".join(random.sample(string.ascii_lowercase + string.ascii_uppercase + '3456789', 24))
        text = "".join(self._text)
        out = BytesIO()
        image.save(out, format=fmt)
        if path:
            image.save(os.path.join(path, name), fmt)
        return name, text, out.getvalue()

    def generate_captcha(self):
        self.initialize()
        return self.captcha("")


captcha = Captcha.instance()


class ImageCode(object):
    """ 验证码处理"""
    def random_color(self):
        """随机颜色"""
        color = (random.randint(32, 127), random.randint(32, 127), random.randint(32, 127))
        return color

    def generate_code(self):
        """生成4位验证码"""
        # ascii_letters是生成所有字母 digits是生成所有数字0-9
        code_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))
        return code_str

    def draw_lines(self, draw, num, width, height):
        """划线"""
        for index in range(num):
            x1 = random.randint(0, width / 2)
            y1 = random.randint(0, height / 2)
            x2 = random.randint(0, width)
            y2 = random.randint(height / 2, height)
            draw.line(((x1, y1), (x2, y2)), fill='black', width=1)
        return 0

    def get_verify_code(self):
        """生成验证码图形"""
        code = self.generate_code()
        # 图片大小120×50
        width, height, num = 120, 50, 4
        # 新图片对象
        images = Image.new('RGB', (width, height), 'white')
        # 字体
        path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/utils/fonts/" + "Arial.ttf"
        font = ImageFont.truetype(path, 40)
        # draw对象
        draw = ImageDraw.Draw(images)
        for value in range(num):
            draw.text((5 + random.randint(-3, 3) + 23 * value, 5 + random.randint(-3, 3)), text=code[value], fill=self.random_color(), font=font)
        # 划线
        self.draw_lines(draw, 2, width, height)
        out = BytesIO()
        images.save(out, 'JPEG')
        return code, out.getvalue()


ImageCode = ImageCode()


if __name__ == '__main__':
    name, text, image = captcha.generate_captcha()
    print(name, text, image)
    # print(os.path.dirname(__file__).split('lib'))
    # dir = os.path.join(os.path.dirname(__file__).split('lib')[0],'utils')
    # print(dir)

