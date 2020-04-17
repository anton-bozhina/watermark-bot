import os
import json
import io
from pathlib import Path
from PIL import Image, ImageEnhance
import logging
from logging.handlers import RotatingFileHandler

WATERMARKS = {
    'white': {
        'name': 'Белый',
        'file': 'Watermark-White.png'
    },
    'silver': {
        'name': 'Серебристый',
        'file': 'Watermark-Silver.png'
    },
    'blue1': {
        'name': 'Синий 1',
        'file': 'Watermark-Blue-1.png'
    },
    'blue2': {
        'name': 'Синий 2',
        'file': 'Watermark-Blue-2.png'
    },
    'blue3': {
        'name': 'Синий 3',
        'file': 'Watermark-Blue-3.png'
    },
    'blue4': {
        'name': 'Синий 4',
        'file': 'Watermark-Blue-4.png'
    },
    'purple': {
        'name': 'Пурпурный',
        'file': 'Watermark-Purple-1.png'
    },
    'orange1': {
        'name': 'Оранжевый 1',
        'file': 'Watermark-Orange-1.png'
    },
    'orange2': {
        'name': 'Оранжевый 2',
        'file': 'Watermark-Orange-2.png'
    },
    'pink': {
        'name': 'Розовый',
        'file': 'Watermark-Pink.png'
    },
    'red1': {
        'name': 'Красный 1',
        'file': 'Watermark-Red-1.png'
    },
    'red2': {
        'name': 'Красный 2',
        'file': 'Watermark-Red-2.png'
    }
}

# Качество миниаютры
THUMBNAIL_QUALITY = 30
QUALITY = 90
# Какой размер марки должен быть
PERCENTAGE = 30
# Отступ от края экрана
INDENT_X = 10
INDENT_Y = 10
# Обрезка марки
CROP_WIDTH = 7
CROP_HEIGHT = 5

MAIN_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
INPUT_PATH = Path(os.path.dirname(os.path.realpath(__file__))) / 'input'
OUTPUT_PATH = Path(os.path.dirname(os.path.realpath(__file__))) / 'output'
WATERMARKS_PATH = Path(os.path.dirname(os.path.realpath(__file__))) / 'watermarks'
INDENT_X -= CROP_WIDTH
INDENT_Y -= CROP_HEIGHT


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(u'' + str(MAIN_PATH / 'createwmark.log'),
                                   maxBytes=1000000, backupCount=10, encoding='utf8')
file_handler.setLevel(logging.INFO)

con_handler = logging.StreamHandler()
con_handler.setLevel(logging.INFO)

formatter = logging.Formatter(u'[%(asctime)s] %(levelname)s - (%(filename)s:%(lineno)d) %(message)s')
file_handler.setFormatter(formatter)
con_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(con_handler)


def get_relative_path(path):
    return Path(path).relative_to(MAIN_PATH)


def adjust_saturation(image, factor):
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(factor)
    return image


def adjust_contrast(image, factor):
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(factor)
    return image


def adjust_brightness(image, factor):
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(factor)
    return image


def adjust_sharpness(image, factor):
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(factor)
    return image


def save_image_settings(chat_id, message_id, key, value):
    save_path = INPUT_PATH / str(chat_id) / (str(message_id) + '.json')

    if not save_path.exists():
        save_path.touch()

    with open(str(save_path), 'r+') as file:
        try:
            file_info = json.load(file)
        except json.decoder.JSONDecodeError:
            file_info = dict()

        file_info[key] = value
        file.seek(0)
        file.write(json.dumps(file_info, indent=2))
        file.truncate()


def load_image_settings(chat_id, message_id, key, default=None):
    save_path = INPUT_PATH / str(chat_id) / (str(message_id) + '.json')

    if not save_path.exists():
        save_path.touch()

    with open(str(save_path), 'r') as file:
        try:
            file_info = json.load(file)
        except json.decoder.JSONDecodeError:
            file_info = dict()

        try:
            return file_info[key]
        except KeyError:
            return default


def make_image(chat_id, message_id, lightweight=True, to_bytes=True, reset=False):
    chat_id = str(chat_id)

    file_name = load_image_settings(chat_id, message_id, 'file', '')
    position = load_image_settings(chat_id, message_id, 'position', 'topleft')
    watermark = load_image_settings(chat_id, message_id, 'watermark', 'Watermark-White.png')

    saturation = load_image_settings(chat_id, message_id, 'saturation', 1)
    contrast = load_image_settings(chat_id, message_id, 'contrast', 1)
    brightness = load_image_settings(chat_id, message_id, 'brightness', 1)
    sharpness = load_image_settings(chat_id, message_id, 'sharpness', 1)

    mark_size = int(load_image_settings(chat_id, message_id, 'mark_size', PERCENTAGE))

    input_image = str(INPUT_PATH / chat_id / file_name)
    watermark_image = str(WATERMARKS_PATH / watermark)

    image = Image.open(input_image)
    imagewidth = image.width
    imageheight = image.height

    if not reset:

        image = adjust_saturation(image, saturation)
        image = adjust_contrast(image, contrast)
        image = adjust_brightness(image, brightness)
        image = adjust_sharpness(image, sharpness)

        mark = Image.open(watermark_image)
        markwidth = mark.width
        markheight = mark.height

        (markwidth, markheight) = (round(imagewidth / 100 * mark_size),
                                   round(markheight / (markwidth / (imagewidth / 100 * mark_size))))
        mark = mark.resize((markwidth, markheight), resample=Image.LANCZOS)

        if position == 'topleft':
            image.paste(mark, (INDENT_X, INDENT_Y), mark)
        elif position == 'topcenter':
            image.paste(mark, (round((imagewidth - markwidth) / 2), INDENT_Y), mark)
        elif position == 'topright':
            image.paste(mark, (imagewidth - markwidth - INDENT_X, INDENT_Y), mark)
        elif position == 'centerleft':
            image.paste(mark, (INDENT_X, round((imageheight - markheight) / 2)), mark)
        elif position == 'center':
            image.paste(mark, (round((imagewidth - markwidth) / 2), round((imageheight - markheight) / 2)), mark)
        elif position == 'centerright':
            image.paste(mark, (imagewidth - markwidth - INDENT_X, round((imageheight - markheight) / 2)), mark)
        elif position == 'bottomleft':
            image.paste(mark, (INDENT_X, imageheight - markheight - INDENT_Y), mark)
        elif position == 'bottomcenter':
            image.paste(mark, (round((imagewidth - markwidth) / 2), imageheight - markheight - INDENT_Y), mark)
        elif position == 'bottomright':
            image.paste(mark, (imagewidth - markwidth - INDENT_X, imageheight - markheight - INDENT_Y), mark)
        else:
            print('Error: ' + position + ' is not a valid position')

    if lightweight:
        if to_bytes:
            byte_io = io.BytesIO()
            image.convert('RGB').save(byte_io, format='JPEG', quality=THUMBNAIL_QUALITY)

            return byte_io.getvalue()
        else:
            output_image = str(OUTPUT_PATH / chat_id / str('T_' + file_name))
            Path(output_image).parent.mkdir(parents=True, exist_ok=True)
            image.convert('RGB').save(output_image, format='JPEG', quality=THUMBNAIL_QUALITY)

            return output_image
    else:
        output_image = str(OUTPUT_PATH / chat_id / file_name)
        Path(output_image).parent.mkdir(parents=True, exist_ok=True)
        image.save(output_image, quality=QUALITY, subsampling=0)

        return output_image
