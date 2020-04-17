import config
from emoji import emojize
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
        # Variables
        events_done = len(model.get_client_ended_events(message.chat.id))
        pending_requests = len(model.get_client_pending_requests(message.chat.id))
        needs_feedback = len(model.get_events_without_feedback(message.chat.id))

        # String for menu
        events_done_str = f'{emojize(" :white_check_mark:", use_aliases=True)}Обслужених подій: {events_done}\n\n'
        pending_requests_str = f'{emojize(" :hourglass_flowing_sand:", use_aliases=True)}Заявок в обробці: {pending_requests}\n'
        needs_feedback_str = f'{emojize(" :star:", use_aliases=True)}Заявок без відгуку: {needs_feedback}\n'
        empty_menu_str = f'Виберіть дію:'

        # Menu text formatting
        msg = f'{emojize(" :green_book:", use_aliases=True)}Головне меню\n' \
              f'{"-" * 20}\n' \
              f'{events_done_str if events_done > 0 else ""}' \
              f'{pending_requests_str if pending_requests > 0 else ""}' \
              f'{needs_feedback_str if needs_feedback > 0 else ""}' \
              f'{empty_menu_str if events_done==0 and needs_feedback==0 and pending_requests==0 else ""}'

        inline_kb = types.InlineKeyboardMarkup()

        # Buttons declaration
        events_archive = types.InlineKeyboardButton(text=f'{emojize(" :open_file_folder:", use_aliases=True)}Переглянути події', callback_data='events_archive')
        check_pending_requests = types.InlineKeyboardButton(text=f'{emojize(" :clipboard:", use_aliases=True)}Переглянути заявки', callback_data='check_pending_requests')
        left_feedback = types.InlineKeyboardButton(text=f'{emojize(" :bar_chart:", use_aliases=True)}Виставити рейтинг', callback_data='left_feedback')
        create_request = types.InlineKeyboardButton(text=f'{emojize(" :pencil2:", use_aliases=True)}Створити заявку', callback_data='create_event_request')
        update = types.InlineKeyboardButton(text=f'{emojize(" :arrows_counterclockwise:", use_aliases=True)}Оновити', callback_data='main_menu')

        # Keyboard formatting
        if events_done > 0:
            inline_kb.row(events_archive)
        if pending_requests > 0:
            inline_kb.row(check_pending_requests)
        if needs_feedback > 0:
            inline_kb.row(left_feedback)
        inline_kb.row(create_request)
        inline_kb.row(update)

        if edit:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=message.message_id,
                                  text=msg)
            bot.edit_message_reply_markup(chat_id=message.chat.id,
                                          message_id=message.message_id,
                                          reply_markup=inline_kb)
        else:
            bot.send_message(chat_id=message.chat.id,
                             text=msg,
                             reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def main_menu(call):
    try:
        show_main_menu(call.message, True)
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
# TODO: fill client contact data
