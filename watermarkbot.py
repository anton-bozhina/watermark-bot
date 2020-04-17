# TODO: С правой стороны ватермар с другой ориентацией

import telebot
import json
import logging
from logging.handlers import RotatingFileHandler
from random import randint
from datetime import date
from pathlib import Path
from telebot import apihelper
from telebot import types

from createwmark import WATERMARKS, INPUT_PATH, OUTPUT_PATH, MAIN_PATH, PERCENTAGE, \
    make_image, get_relative_path, save_image_settings, load_image_settings

bot = telebot.TeleBot('1234567890')
apihelper.proxy = {'https': 'socks5://10.10.10.5:9050'}

telebot.logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(u'' + str(MAIN_PATH / 'createwmark.log'),
                                   maxBytes=1000000, backupCount=10, encoding='utf8')
file_handler.setLevel(logging.INFO)

con_handler = logging.StreamHandler()
con_handler.setLevel(logging.INFO)

formatter = logging.Formatter(u'[%(asctime)s] %(levelname)s - (%(filename)s:%(lineno)d) %(message)s')
file_handler.setFormatter(formatter)
con_handler.setFormatter(formatter)

telebot.logger.addHandler(file_handler)
telebot.logger.addHandler(con_handler)

MESSAGES = {
    'start': 'Привет, {}! ☺ Очень рада, что ты захотел воспользоваться моей помощью!\n\n'
             'Отправь мне изображение 🌄 и я поставлю на нем красивый отпечаток. '
             'Главное не забудь, что временные фотографии будут в плохом качестве, '
             'для того что бы получить фотографию в исходном качестве, нажмите "💾 Сохранить". '
             'Так же фотографии только одни сутки доступны для редактирования, '
             'потом можно будет только скачать готовый результат.',
    'whitelist': 'Извини, {}, но мне нельзя с тобой общаться... 😢',
}

STICKERS = {
    'hello': 'CAACAgIAAxkBAAMDXo7fcQcL3jCR_xQ3PHRMr68ighQAAgEBAAJWnb0KIr6fDrjC5jQYBA',
    'shrugging': 'CAACAgIAAxkBAANAXo7vD3zOBMuAO74Z4Wb7SaIXUjAAAvkAA1advQqVZW6rKisbNhgE',
}

RANDOM_STICKERS = [
    'CAACAgIAAxkBAAIBzV6QKUnFa1e4pWZDFyk-g2a6uQvpAALyAANWnb0KEJ2LdlN60mQYBA',
    'CAACAgIAAxkBAAIBzl6QKU08xBsUIjyjmnW7ItjYY7ihAAIEAQACVp29Ct4E0XpmZvdsGAQ',
    'CAACAgIAAxkBAAIBz16QKU6F5RWkr4n99CMlVmWljqoCAAL-AANWnb0K2gRhMC751_8YBA',
    'CAACAgIAAxkBAAIB0F6QKVH1OWL58kF4M5twmXFdEUkvAAIBAQACVp29CiK-nw64wuY0GAQ',
    'CAACAgIAAxkBAAIB0V6QKVU0YvK6ynyWKlMpMM4TEYUMAAL0AANWnb0KEViw9dn9VUkYBA',
    'CAACAgIAAxkBAAIB0l6QKVcKA3eCLsrc44NdROj3mIlVAAL2AANWnb0K99tOIUA-pYoYBA',
    'CAACAgIAAxkBAAIB016QKVhS1XZtEfZ-oL11wy9LIYIEAAL3AANWnb0KC3IkHUj0DTAYBA',
    'CAACAgIAAxkBAAIB1F6QKVwhVAdpj6HorX1p6H-ATZwmAAIHAQACVp29Cr-3JmEik7miGAQ',
    'CAACAgIAAxkBAAIB1V6QKV8D2wxZknlShRLvMOopSrR1AAIFAQACVp29Crfk_bYORV93GAQ',
    'CAACAgIAAxkBAAIB1l6QKWN_y2B82o1nNGDWcLUx_04KAAL6AANWnb0KR976l3F0cQEYBA',
    'CAACAgIAAxkBAAIB116QKW_yvJI7dLE4mM2rMVLp8731AAINAQACVp29Ckb9Qx0FRNeXGAQ',
    'CAACAgIAAxkBAAIB2F6QKXThZZWS1jrpL3TmmU-na-BGAALaAQACVp29CpusqfDD0FWIGAQ',
    'CAACAgIAAxkBAAIB2V6QKXf1AokjReBB6ycj0Ji1s1gjAAICAQACVp29Ck7ibIHLQOT_GAQ',
]

POSITIONS = {
    'topleft': '↖',
    'topcenter': '️⬆',
    'topright': '↗',
    'centerleft': '️️⬅️',
    'center': '⏺',
    'centerright': '➡',
    'bottomleft': '↙',
    'bottomcenter': '️️⬇',
    'bottomright': '️↘️',
}


# Ищем и удаляем старые файлы
def delete_old_files(chat_id):
    work_dir = Path(OUTPUT_PATH / str(chat_id))
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    for file in work_dir.iterdir():
        timestamp = date.fromtimestamp(file.stat().st_mtime)
        if date.today() != timestamp:
            file.unlink()

    work_dir = Path(INPUT_PATH / str(chat_id))
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    for file in work_dir.iterdir():
        timestamp = date.fromtimestamp(file.stat().st_mtime)
        if date.today() != timestamp:
            file.unlink()


# Тут определяются какие кнопки будут показаны в меню выбора позиции, отправляется следующая страница,
# имя файла и положение
def position_markup(call_data=''):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(POSITIONS['topleft'],
                                   callback_data='empty' if call_data == 'position:topleft'
                                   else 'position:topleft'),
        types.InlineKeyboardButton(POSITIONS['topcenter'],
                                   callback_data='empty' if call_data == 'position:topcenter'
                                   else 'position:topcenter'),
        types.InlineKeyboardButton(POSITIONS['topright'],
                                   callback_data='empty' if call_data == 'position:topright'
                                   else 'position:topright'),
    )
    markup.row(
        types.InlineKeyboardButton(POSITIONS['centerleft'],
                                   callback_data='empty' if call_data == 'position:centerleft'
                                   else 'position:centerleft'),
        types.InlineKeyboardButton(POSITIONS['center'],
                                   callback_data='empty' if call_data == 'position:center'
                                   else 'position:center'),
        types.InlineKeyboardButton(POSITIONS['centerright'],
                                   callback_data='empty' if call_data == 'position:centerright'
                                   else 'position:centerright'),
    )
    markup.row(
        types.InlineKeyboardButton(POSITIONS['bottomleft'],
                                   callback_data='empty' if call_data == 'position:bottomleft'
                                   else 'position:bottomleft'),
        types.InlineKeyboardButton(POSITIONS['bottomcenter'],
                                   callback_data='empty' if call_data == 'position:bottomcenter'
                                   else 'position:bottomcenter'),
        types.InlineKeyboardButton(POSITIONS['bottomright'],
                                   callback_data='empty' if call_data == 'position:bottomright'
                                   else 'position:bottomright'),
    )
    markup.row(
        types.InlineKeyboardButton('🔽 Скачать', callback_data='download:edit_position'),
        types.InlineKeyboardButton('Дальше ▶️', callback_data='edit_watermark'),
    )
    return markup


# Тут формирутеся меню изменения цвета
def color_markup(call_data=''):
    markup = types.InlineKeyboardMarkup()

    markup.row_width = 2

    row_colors = list()
    for name in list(WATERMARKS.values()):
        # Защита от повторного использования тех же пунктов меню
        if call_data != name['file']:
            row_colors.append(types.InlineKeyboardButton(name['name'],
                                                         callback_data='watermark:' + name['file']))
        else:
            row_colors.append(types.InlineKeyboardButton(text='⚜️ ' + name['name'] + ' ⚜️', callback_data='empty'))
    markup.add(*row_colors)

    # Кнопка назад может передавать сколько угодно параметров, там нужен только первый, имя файла.
    # Кнопка загрузки должна передавать все параметры, в том числе и цвет.
    markup.row(
        types.InlineKeyboardButton('◀️️ Назад', callback_data='edit_position'),
        types.InlineKeyboardButton('🔽 Скачать', callback_data='download:edit_watermark'),
        types.InlineKeyboardButton('Дальше ▶️', callback_data='edit_image')
    )

    return markup


def image_markup(call_data=''):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('️◀️',
                                   callback_data='image:saturation:reduce'),
        types.InlineKeyboardButton('Цвет',
                                   callback_data='image:saturation:reset'),
        types.InlineKeyboardButton('▶',
                                   callback_data='image:saturation:add'),
    )
    markup.row(
        types.InlineKeyboardButton('️◀️',
                                   callback_data='image:contrast:reduce'),
        types.InlineKeyboardButton('Контраст',
                                   callback_data='image:contrast:reset'),
        types.InlineKeyboardButton('▶',
                                   callback_data='image:contrast:add'),
    )
    markup.row(
        types.InlineKeyboardButton('️◀️',
                                   callback_data='image:brightness:reduce'),
        types.InlineKeyboardButton('Яркость',
                                   callback_data='image:brightness:reset'),
        types.InlineKeyboardButton('▶',
                                   callback_data='image:brightness:add'),
    )
    markup.row(
        types.InlineKeyboardButton('️◀️',
                                   callback_data='image:sharpness:reduce'),
        types.InlineKeyboardButton('Резкость',
                                   callback_data='image:sharpness:reset'),
        types.InlineKeyboardButton('▶',
                                   callback_data='image:sharpness:add'),
    )
    markup.row(
        types.InlineKeyboardButton('🔅',
                                   callback_data='image:mark_size:20'),
        types.InlineKeyboardButton('Размер',
                                   callback_data='image:mark_size:30'),
        types.InlineKeyboardButton('🔆',
                                   callback_data='image:mark_size:40'),
    )
    markup.row(
        types.InlineKeyboardButton('◀️️ Назад', callback_data='edit_watermark'),
        types.InlineKeyboardButton('🔽 Скачать', callback_data='download:edit_position'),
    )
    return markup


# Когда нажата кнопка скачать, то появляется меню назад. Сделано, что бы меньше места было занято.
def download_markup(call_data):
    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton('✏️ Изменить', callback_data=call_data),
    )

    return markup


def edit_message(chat_id=None, message_id=None, reply_markup=None, media=None):
    try:
        bot.edit_message_media(chat_id=chat_id, message_id=message_id,
                               reply_markup=reply_markup,
                               media=media)
    except Exception as e:
        telebot.logger.error(e)


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id

    telebot.logger.info('User {name} ({chat_id}) start using bot.'.format(name=message.chat.username,
                                                                          chat_id=chat_id))

    bot.send_chat_action(chat_id, 'typing')
    bot.send_message(chat_id, MESSAGES['start'].format(message.chat.first_name))
    bot.send_sticker(chat_id, STICKERS['hello'])


def content_check(message):
    return message.document is not None and message.document.mime_type == 'image/jpeg' or \
           message.document is not None and message.document.mime_type == 'image/png' or \
           message.photo is not None


@bot.message_handler(func=content_check, content_types=['photo', 'document'])
def save_photo(message):
    # Телеграм сжимает фотки в 2-3 размера, поэтому мы берем только самую большую (-1)
    chat_id = message.chat.id

    bot.send_chat_action(chat_id, 'typing')

    if message.document is None:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    bot.delete_message(chat_id=chat_id, message_id=message.message_id)

    file_file = bot.get_file(file_id)

    downloaded_file = bot.download_file(file_file.file_path)
    
    last_message = bot.send_photo(chat_id, downloaded_file,
                                  reply_markup=position_markup(),
                                  caption='📝 В каком месте будет печать?')

    file_name = str(last_message.message_id) + Path(file_file.file_path).suffix
    save_path = str(INPUT_PATH / str(chat_id) / file_name)

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    save_image_settings(chat_id, last_message.message_id, 'file_id', file_id)
    save_image_settings(chat_id, last_message.message_id, 'file', file_name)

    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)

        telebot.logger.info('Save image to {image} from {name} ({chat_id}).'.format(name=message.chat.username,
                                                                                    image=get_relative_path(save_path),
                                                                                    chat_id=message.chat.id))
    Path(MAIN_PATH / 'messages').mkdir(parents=True, exist_ok=True)
    
    with open(str(MAIN_PATH / 'messages' / str(chat_id)), 'w+') as last_message_file:
        last_message_file.write(json.dumps(last_message.json, indent=2))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    call_data = call.data

    if call_data.startswith('edit_position'):
        if Path(INPUT_PATH / str(chat_id) / (str(message_id) + '.json')).is_file():
            output_file = make_image(chat_id, message_id)

            edit_message(chat_id=chat_id, message_id=message_id,
                         reply_markup=position_markup(call_data),
                         media=types.InputMediaPhoto(output_file, caption='📝 В каком месте будет печать?'))
        else:
            bot.edit_message_caption('🥺 Изменить файл уже нельзя...',
                                     chat_id=chat_id, message_id=message_id)

    elif call_data.startswith('position:'):
        if Path(INPUT_PATH / str(chat_id) / (str(message_id) + '.json')).is_file():
            save_image_settings(chat_id, message_id,
                                key=call_data.split(':')[0],
                                value=call_data.split(':')[1])

            output_file = make_image(chat_id, message_id)

            edit_message(chat_id=chat_id, message_id=message_id,
                         reply_markup=position_markup(call_data),
                         media=types.InputMediaPhoto(output_file, caption='📝 В каком месте будет печать?'))
        else:
            bot.edit_message_caption('🥺 Изменить файл уже нельзя...',
                                     chat_id=chat_id, message_id=message_id)

    elif call_data.startswith('edit_watermark'):
        if Path(INPUT_PATH / str(chat_id) / (str(message_id) + '.json')).is_file():

            output_file = make_image(chat_id, message_id)

            edit_message(chat_id=chat_id, message_id=message_id,
                         reply_markup=color_markup(load_image_settings(chat_id, message_id,
                                                                       'watermark', 'Watermark-White.png')),
                         media=types.InputMediaPhoto(output_file, caption='🖍 Какого цвета сделаем печать?'))
        else:
            bot.edit_message_caption('🥺 Изменить файл уже нельзя...',
                                     chat_id=chat_id, message_id=message_id)

    elif call_data.startswith('watermark:'):
        if Path(INPUT_PATH / str(chat_id) / (str(message_id) + '.json')).is_file():
            save_image_settings(chat_id, message_id,
                                key=call_data.split(':')[0],
                                value=call_data.split(':')[1])

            output_file = make_image(chat_id, message_id)

            edit_message(chat_id=chat_id, message_id=message_id,
                         reply_markup=color_markup(call_data.split(':')[1]),
                         media=types.InputMediaPhoto(output_file, caption='🖍 Какого цвета сделаем печать?'))
        else:
            bot.edit_message_caption('🥺 Изменить файл уже нельзя...',
                                     chat_id=chat_id, message_id=message_id)

    elif call_data.startswith('edit_image'):
        if Path(INPUT_PATH / str(chat_id) / (str(message_id) + '.json')).is_file():

            output_file = make_image(chat_id, message_id)

            edit_message(chat_id=chat_id, message_id=message_id,
                         reply_markup=image_markup(),
                         media=types.InputMediaPhoto(output_file, caption='💈 Какой параметр изменить?'))
        else:
            bot.edit_message_caption('🥺 Изменить файл уже нельзя...',
                                     chat_id=chat_id, message_id=message_id)

    elif call_data.startswith('image:'):
        if Path(INPUT_PATH / str(chat_id) / (str(message_id) + '.json')).is_file():
            if call_data.split(':')[1] == 'saturation':
                factor = load_image_settings(chat_id, message_id, 'saturation', 1)
                abjustment = call_data.split(':')[2]

                if abjustment == 'add':
                    factor += 0.1
                    bot.answer_callback_query(call.id, 'Насыщенность увеличена')
                elif abjustment == 'reduce':
                    factor -= 0.1
                    bot.answer_callback_query(call.id, 'Насыщенность уменьшена')
                elif abjustment == 'reset':
                    factor = 1
                    bot.answer_callback_query(call.id, 'Насыщенность сброшена')

                save_image_settings(chat_id, message_id,
                                    key='saturation',
                                    value=factor)

            elif call_data.split(':')[1] == 'contrast':
                factor = load_image_settings(chat_id, message_id, 'contrast', 1)
                abjustment = call_data.split(':')[2]

                if abjustment == 'add':
                    factor += 0.05
                    bot.answer_callback_query(call.id, 'Контраст увеличен')
                elif abjustment == 'reduce':
                    factor -= 0.05
                    bot.answer_callback_query(call.id, 'Контраст уменьшен')
                elif abjustment == 'reset':
                    factor = 1
                    bot.answer_callback_query(call.id, 'Контраст сброшен')

                save_image_settings(chat_id, message_id,
                                    key='contrast',
                                    value=factor)

            elif call_data.split(':')[1] == 'brightness':
                factor = load_image_settings(chat_id, message_id, 'brightness', 1)
                abjustment = call_data.split(':')[2]

                if abjustment == 'add':
                    factor += 0.05
                    bot.answer_callback_query(call.id, 'Яркость увеличена')
                elif abjustment == 'reduce':
                    factor -= 0.05
                    bot.answer_callback_query(call.id, 'Яркость уменьшена')
                elif abjustment == 'reset':
                    factor = 1
                    bot.answer_callback_query(call.id, 'Яркость сброшена')

                save_image_settings(chat_id, message_id,
                                    key='brightness',
                                    value=factor)

            elif call_data.split(':')[1] == 'sharpness':
                factor = load_image_settings(chat_id, message_id, 'sharpness', 1)
                abjustment = call_data.split(':')[2]

                if abjustment == 'add':
                    factor += 0.5
                    bot.answer_callback_query(call.id, 'Резкость увеличена')
                elif abjustment == 'reduce':
                    factor -= 0.5
                    bot.answer_callback_query(call.id, 'Резкость уменьшена')
                elif abjustment == 'reset':
                    factor = 1
                    bot.answer_callback_query(call.id, 'Резкость сброшена')

                save_image_settings(chat_id, message_id,
                                    key='sharpness',
                                    value=factor)

            elif call_data.split(':')[1] == 'mark_size':

                bot.answer_callback_query(call.id, 'Размер печати изменен')

                save_image_settings(chat_id, message_id,
                                    key='mark_size',
                                    value=call_data.split(':')[2])

            output_file = make_image(chat_id, message_id)
            try:
                edit_message(chat_id=chat_id, message_id=message_id,
                             reply_markup=image_markup(),
                             media=types.InputMediaPhoto(output_file, caption='💈 Какой параметр изменить?'))
            except Exception as e:
                telebot.logger.error(e)
        else:
            bot.edit_message_caption('🥺 Изменить файл уже нельзя...',
                                     chat_id=chat_id, message_id=message_id)

    elif call_data.startswith('download'):
        # Если нажата кнопка загрузки
        bot.send_chat_action(chat_id, 'upload_photo')

        output_file = make_image(chat_id, message_id, lightweight=False)

        photo = open(output_file, 'rb')

        telebot.logger.info('Send finish image ({data}) to {name} ({chat_id}).'.format(name=call.message.chat.username,
                                                                                       data=call_data,
                                                                                       chat_id=chat_id))
        edit_message(chat_id=chat_id, message_id=message_id,
                     reply_markup=download_markup(call_data.split(':')[1]),
                     media=types.InputMediaDocument(photo,
                                                    caption='🎉 Готово, можешь скачать результат!'))

        # Это все необходимо, что бы отслеживать последнее сообщение
        # и если оно стикер, то стикеры больше не будут отправляться...
        if not Path(MAIN_PATH / 'messages' / str(chat_id)).exists():
            Path(MAIN_PATH / 'messages' / str(chat_id)).touch()

        with open(str(MAIN_PATH / 'messages' / str(chat_id)), 'r+') as last_message_file:
            try:
                last_message = json.load(last_message_file)
            except json.decoder.JSONDecodeError:
                last_message = dict()

            if last_message.get('sticker') is None:
                if randint(0, 5) == 0:
                    last_message = bot.send_sticker(chat_id=chat_id,
                                                    data=RANDOM_STICKERS[randint(0, len(RANDOM_STICKERS)-1)])
                    last_message_file.seek(0)
                    last_message_file.write(json.dumps(last_message.json, indent=2))
                    last_message_file.truncate()

        # Удаляем старые файлы
        delete_old_files(chat_id)
    elif call_data.startswith('empty'):
        # Защита от повторного использования тех же пунктов меню
        bot.answer_callback_query(call.id, 'Этот параметр уже выбран! Попробуй другой 😉')


def main():
    bot.infinity_polling(timeout=60)


if __name__ == '__main__':
    main()
