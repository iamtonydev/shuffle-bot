# -*- coding: utf-8 -*-
import telebot
from telebot import types
import random
from config import API_KEY


bot = telebot.TeleBot(API_KEY)


class User:

    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.q_players = None
        self.q_commands = None
        self.players_name = []


USERS = {}


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if 'start' in message.text:
        chat_id = message.chat.id
        USERS[chat_id] = User(chat_id)
        bot.send_message(message.chat.id, """\
        Привет! Я помогу вам разбиться на команды.""")

        markup = types.InlineKeyboardMarkup(row_width=1)
        but = types.InlineKeyboardButton("Да", callback_data='yes')
        markup.add(but)

        bot.send_message(message.chat.id, 'Хотите начать?', reply_markup=markup)
    elif 'help' in message.text:
        bot.send_message(message.chat.id, 'Чтобы перезапустить меня, отправьте "/start"')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline_keyboard(call):
    if call.data == 'yes':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Хотите начать?', reply_markup=None)
        msg = bot.send_message(call.message.chat.id, 'Сколько игроков нужно поделить?')
        bot.register_next_step_handler(msg, process_players_step)


def process_players_step(message):
    if not message.text.isdigit():
        msg = bot.reply_to(message, 'Нужно ввести количество игроков цифрой')
        bot.register_next_step_handler(msg, process_players_step)
        return
    chat_id = message.chat.id
    USERS[chat_id].q_players = int(message.text)
    msg = bot.send_message(message.chat.id, 'Хорошо. На сколько команд вас нужно поделить?')
    bot.register_next_step_handler(msg, process_commands_step)


def process_commands_step(message):
    if not message.text.isdigit():
        msg = bot.reply_to(message, 'Нужно ввести количество команд цифрой')
        bot.register_next_step_handler(msg, process_commands_step)
        return
    chat_id = message.chat.id
    USERS[chat_id].q_commands = int(message.text)
    msg = bot.send_message(message.chat.id, 'Теперь введите имя 1 игрока')
    bot.register_next_step_handler(msg, process_list_step)


def process_list_step(message):
    chat_id = message.chat.id
    if (len(USERS[chat_id].players_name) + 1) < (int(USERS[chat_id].q_players)):
        USERS[chat_id].players_name.append(message.text)
        msg = bot.send_message(message.chat.id, 'Введите имя следующего игрока')
        bot.register_next_step_handler(msg, process_list_step)
    else:
        USERS[chat_id].players_name.append(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        but = types.KeyboardButton("Перемешать")
        markup.add(but)

        msg = bot.send_message(message.chat.id, 'Все готово. Чтобы получить результат, нажми "Перемешать"',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, process_shuffle_step)


def process_shuffle_step(message):
    chat_id = message.chat.id

    x = USERS[chat_id].q_players
    y = USERS[chat_id].q_commands
    players = list(USERS[chat_id].players_name)

    q_in_team = x // y

    for _ in range(0, y):
        team = random.sample(players, q_in_team)
        msg = " ".join(map(str, team))
        players = list(set(players) - set(team))
        bot.send_message(message.chat.id, f"{msg}")

    if len(players) == 1:
        bot.send_message(message.chat.id, f"А этот {''.join(map(str, players))} — лишний. "
                                          f"Пусть выберет команду по желанию.")
    elif len(players) > 1:
        bot.send_message(message.chat.id, f"А эти {''.join(map(str, players))} — лишние. "
                                          f"Пусть выберут команду по желанию. Или будут в отдельной.")

    markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton("Перемешать еще раз")
    but2 = types.KeyboardButton("Нет")
    markup2.add(but1, but2)

    msg = bot.send_message(message.chat.id, 'Желаете перемешать еще раз?', reply_markup=markup2)
    bot.register_next_step_handler(msg, process_again_step)


def process_again_step(message):
    if 'Перемешать еще раз' in message.text:
        process_shuffle_step(message)
    elif 'Нет' in message.text:
        bot.send_message(message.chat.id, 'Главное не участие, а победа!',
                         reply_markup=types.ReplyKeyboardRemove())


bot.polling()
