import config
from model import Model
from log_handler import LogHandler
import telebot
from telebot import types
import sys
import time

bot = telebot.TeleBot(config.TOKEN)
logger = LogHandler()
model = Model(logger)


def init_controller():
    """
    Controller initialization
    :return: None
    """
    try:
        bot.polling(none_stop=True)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'sys')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'sys')
        time.sleep(5)


def show_main_menu(message, edit=False):
    try:
        bot.send_message(chat_id=message.chat.id, text='menu')
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.message_handler(commands=['start'])
def start_command_handler(message):
    try:
        msg = ''
        client = model.is_user_registered(message.chat.id)
        if client:
            msg = f'Вітаю, {client[2]}!'
            bot.send_message(chat_id=message.chat.id,
                             text=msg)
            show_main_menu(message)
        else:
            msg = 'Вітаю! Схоже це ваш перший візит до компанії \'Five star\'! Введіть своє ім\'я, і ми продовжимо:'
            bot.send_message(chat_id=message.chat.id,text=msg)

            bot.register_next_step_handler_by_chat_id(message.chat.id, set_client_name)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def set_client_name(message):
    """
    registers client in system, and enters his name to db
    :param message: message instance
    :return: None
    """
    try:
        model.register_client_name(message.chat.id, message.from_user.username, message.text)
        bot.send_message(chat_id=message.chat.id, text='Ваше ім\'я успішно внесено:)')
        show_main_menu(message)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')