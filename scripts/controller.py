import datetime
import calendar
import config
from emoji import emojize
from model import Model
from log_handler import LogHandler
import telebot
from telebot import types
from socket_handler import SocketHandler
import sys
import time

bot = telebot.TeleBot(config.TOKEN)
logger = LogHandler()
sock_handler = SocketHandler(logger)
model = Model(logger, sock_handler)

# Reply markup buttons for calendar
kb_mon = types.InlineKeyboardButton(text='Пн', callback_data='day_name')
kb_tue = types.InlineKeyboardButton(text='Вт', callback_data='day_name')
kb_wed = types.InlineKeyboardButton(text='Ср', callback_data='day_name')
kb_thu = types.InlineKeyboardButton(text='Чт', callback_data='day_name')
kb_fri = types.InlineKeyboardButton(text='Пт', callback_data='day_name')
kb_sat = types.InlineKeyboardButton(text='Сб', callback_data='day_name')
kb_sun = types.InlineKeyboardButton(text='Нд', callback_data='day_name')

month_names = {1: 'Січень',
               2: 'Лютий',
               3: 'Березень',
               4: 'Квітень',
               5: 'Травень',
               6: 'Червень',
               7: 'Липень',
               8: 'Серпень',
               9: 'Вересень',
               10: 'Жовтень',
               11: 'Листопад',
               12: 'Грудень'}

ev_req_for_contact_updating = {}


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
    except KeyboardInterrupt:
        exit(0)


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
              f'{empty_menu_str if events_done == 0 and needs_feedback == 0 and pending_requests == 0 else ""}'

        inline_kb = types.InlineKeyboardMarkup()

        # Buttons declaration
        events_archive = types.InlineKeyboardButton(
            text=f'{emojize(" :open_file_folder:", use_aliases=True)}Переглянути події', callback_data='events_archive_page:0')
        check_pending_requests = types.InlineKeyboardButton(
            text=f'{emojize(" :clipboard:", use_aliases=True)}Переглянути заявки',
            callback_data='check_pending_requests')
        left_feedback = types.InlineKeyboardButton(text=f'{emojize(" :bar_chart:", use_aliases=True)}Виставити рейтинг',
                                                   callback_data='left_feedback')
        create_request = types.InlineKeyboardButton(text=f'{emojize(" :pencil2:", use_aliases=True)}Створити заявку',
                                                    callback_data='create_event_request')
        update = types.InlineKeyboardButton(text=f'{emojize(" :arrows_counterclockwise:", use_aliases=True)}Оновити',
                                            callback_data='main_menu')

        # Keyboard formatting
        if events_done > 0:
            inline_kb.row(events_archive)
        if pending_requests > 0:
            inline_kb.row(check_pending_requests)
        if needs_feedback > 0:
            inline_kb.row(left_feedback)
        inline_kb.row(create_request)
        inline_kb.row(update)

        message_res_id = 0
        if edit:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=message.message_id,
                                  text=msg)
            bot.edit_message_reply_markup(chat_id=message.chat.id,
                                          message_id=message.message_id,
                                          reply_markup=inline_kb)
            message_res_id = message.message_id
        else:
            message_res_id = bot.send_message(chat_id=message.chat.id,
                                              text=msg,
                                              reply_markup=inline_kb).message_id
        model.set_client_last_message_id(message.chat.id, message_res_id)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.message_handler(commands=['menu'])
def handle_menu_command(message):
    try:
        show_main_menu(message, False)
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


@bot.callback_query_handler(func=lambda call: call.data == 'check_pending_requests')
def check_pending_requests_handler(call):
    try:
        msg = f'Виберіть заявку, яку хотіли б переглянути:'
        inline_kb = types.InlineKeyboardMarkup()

        requests = model.get_client_pending_requests_extended(call.message.chat.id)

        if len(requests) == 0:
            msg = 'На жаль, у вас ще немає активних заявок! ' \
                  'Щоб створити нову заявку ви можете скористатись кнопкою в головному меню'
        else:
            for request in requests:
                inline_kb.row(types.InlineKeyboardButton(text=f'{request[7]}, подана {request[2]}',
                                                         callback_data=f'show_event_request_id:{request[0]}'))

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню',
                                          callback_data='main_menu')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('show_event_request_id:')) > 1)
def show_event_request_id_handler(call):
    try:
        event_request_id = call.data.split('show_event_request_id:')[1]

        show_event_request_details(call.message, event_request_id, edit_message=True)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: call.data == 'create_event_request')
def create_event_request_handler(call):
    try:
        msg = f'Створення заявки на проведення подію. Введіть назву події:'

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg)

        bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_event_title)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def get_event_title(message):
    try:
        event_request_id = model.create_event(message.text, message.chat.id)
        bot.send_message(chat_id=message.chat.id,
                         text='Заявку на подію зареєстровано! Для подання її на розгляд, '
                              'необхідно внести ще деякі дані')
        show_event_request_details(message, event_request_id)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def check_if_request_have_required_data(func):
    """
    Decorator, which wraps function
    :param func: function needed to be wrapped
    :return: wrapped function
    """
    def inner_func(message, event_request_id, edit_message=False):
        """
        Checks if client already filled all required data about event (date starts, date ends and number of guests)
        :param message: message instance
        :param event_request_id: event request id
        :param edit_message:boolean indicator which shows if  message needs to be edited
                        (text and reply markup of parent message). False by default
        :return:None
        """
        event_request_info = [x for x in model.get_client_pending_requests_extended(message.chat.id) if x[0] == int(event_request_id)][0]
        # generator expression to get client pending request which request id = event_request_id

        if event_request_info[9] is not None and event_request_info[10] is not None and event_request_info[13] is not None:
            func(message, event_request_info, edit_message, requires_satisfied=True)
        else:
            func(message, event_request_info, edit_message, requires_satisfied=False)
    return inner_func


@check_if_request_have_required_data
def show_event_request_details(message, event_request_info, edit_message=False, requires_satisfied=False):
    """
    Shows pending event request
    :param message: message instance
    :param event_request_info: event request information.
                               !!! P.S. passed here from decorator, but in the method call,
                                you should specify event request id :) !!!
    :param edit_message: boolean indicator which shows if  message needs to be edited
                        (text and reply markup of parent message). False by default
    :param requires_satisfied: boolean indicator which shows if all requirements satisfied,
                             so client cat go back until he fills all required fields
    :return: None
    """
    try:
        # strings with text about event request data
        creating_request_str = f'Для продовження роботи необхідно внести головні дані, ' \
                               f'а саме дати початку {emojize(":clock4:", use_aliases=True)} ' \
                               f'і кінця {emojize(":clock430:", use_aliases=True)} події, ' \
                               f'а також кількість гостей {emojize(":tophat:", use_aliases=True)}!\n'

        created_request_date_str = f'{emojize(" :boom:", use_aliases=True)}Заявку подано:{event_request_info[2]}'
        request_processed_str = f'{emojize(" :heavy_multiplication_x:" if event_request_info[4] != 1 else ":heavy_check_mark:", use_aliases=True)}' \
                                f'Заявку {"опрацьовано" if event_request_info[4] == 1 else "не опрацьовано"}'
        event_title_str = f'{emojize(" :boom:", use_aliases=True)}Назва події: {event_request_info[7]}'
        event_location_str = f'{emojize(" :round_pushpin:", use_aliases=True)}Місце проведення: {event_request_info[8] if event_request_info[8] is not None else "не зазначено"}'
        date_starts_str = f'{emojize(":clock4:", use_aliases=True)}Дата початку: {event_request_info[9] if event_request_info[9] is not None else "не зазначено"}'
        date_ends_str = f'{emojize(" :clock430:", use_aliases=True)}Дата закінчення: {event_request_info[10] if event_request_info[10] is not None else "не зазначено"}'
        event_type_str = f'{emojize(" :grey_question:", use_aliases=True)}Тип події: {[x[1] for x in model.get_event_types() if x[0] == event_request_info[11]][0] if event_request_info[11] is not None else "не зазначено"}'
        event_class_str = f'{emojize(" :sparkles:", use_aliases=True)}Клас події: {[x[1] for x in model.get_event_classes() if x[0] == event_request_info[12]][0] if event_request_info[12] is not None else "не зазначено"}'
        guests_str = f'{emojize(" :tophat:", use_aliases=True)}Кількість гостей: {event_request_info[13] if event_request_info[13] is not None else "не зазначено"}'

        msg = f'{emojize(" :pencil2:", use_aliases=True)} Створення заявки на проведення події\n' \
              f'{"-" * 20}\n' \
              f'{creating_request_str if not requires_satisfied else ""}' \
              f'{created_request_date_str}\n' \
              f'{request_processed_str}\n' \
              f'{"-" * 20}\n' \
              f'{event_title_str}\n' \
              f'{event_location_str}\n' \
              f'{date_starts_str}\n' \
              f'{date_ends_str}\n' \
              f'{event_type_str}\n' \
              f'{event_class_str}\n' \
              f'{guests_str}\n'

        inline_kb = types.InlineKeyboardMarkup()

        # Buttons implementing
        set_event_title = types.InlineKeyboardButton(text=f'{emojize(" :boom:", use_aliases=True)}Внести назву',
                                                     callback_data=f'update_event_title_ev_id:{event_request_info[5]}')

        set_event_location = types.InlineKeyboardButton(
            text=f'{emojize(" :round_pushpin:", use_aliases=True)}Внести місце проведення',
            callback_data=f'update_event_location_ev_id:{event_request_info[5]}')

        set_date_starts = types.InlineKeyboardButton(text=f'{emojize(":clock4:", use_aliases=True)}Внести дату початку',
                                                     callback_data=f'update_event_date_starts_ev_id:{event_request_info[5]}')

        set_date_ends = types.InlineKeyboardButton(
            text=f'{emojize(":clock430:", use_aliases=True)}Внести дату закінчення',
            callback_data=f'update_event_date_ends_ev_id:{event_request_info[5]}')

        set_event_type = types.InlineKeyboardButton(
            text=f'{emojize(" :grey_question:", use_aliases=True)}Внести тип події',
            callback_data=f'update_event_type_ev_id:{event_request_info[5]}')

        set_event_class = types.InlineKeyboardButton(
            text=f'{emojize(" :sparkles:", use_aliases=True)}Внести клас події',
            callback_data=f'update_event_class_ev_id:{event_request_info[5]}')

        set_number_of_guests = types.InlineKeyboardButton(
            text=f'{emojize(" :tophat:", use_aliases=True)}Внести кількість гостей',
            callback_data=f'update_event_number_of_guests_ev_id:{event_request_info[5]}')

        next = types.InlineKeyboardButton(text=f'{emojize(" :arrow_right:", use_aliases=True)}Далі',
                                          callback_data=f'complete_request_registration_ev_req_id:{event_request_info[0]}')

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню',
                                          callback_data='main_menu')

        inline_kb.row(set_event_title, set_event_location)
        inline_kb.row(set_date_starts)
        inline_kb.row(set_date_ends)
        inline_kb.row(set_event_type, set_event_class)
        inline_kb.row(set_number_of_guests)

        if requires_satisfied and event_request_info[4] == -1:  # needs to make client enter all needed data
            inline_kb.row(next)
        if event_request_info[4] != -1:
            inline_kb.row(back)

        if edit_message:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=message.message_id,
                                  text=msg,
                                  reply_markup=inline_kb)
        else:
            bot.send_message(chat_id=message.chat.id,
                             text=msg,
                             reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_date_starts_ev_id:')) > 1)
def update_event_date_starts_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_date_starts_ev_id:')[1])
        now = datetime.datetime.now()
        msg = f'Виберіть дату початку події:'
        inline_kb = generate_calendar_keyboard(now.year, now.month, False, True, 0, event_id)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def generate_calendar_keyboard(year, r_month, prev_m, next_m, what_date, ev_id):
    """
    Generates inline calendar keyboard, for user friendly date input
    :param year: year of period
    :param month: month of period
    :param prev_m: boolean indicator, if button previous month needs
    :param next_m: boolean indicator, if button next month needs
    :param what_date: 0 - 'date starts event', 1 - 'date ends event
    :param ev_id: event id
    :return: inline keyboard instance
    """
    try:
        date = datetime.datetime.now()
        month = calendar.monthcalendar(year, r_month)

        if date.month == r_month:
            for i in range(len(month)):
                for j in range(len(month[i])):
                    if month[i][j] < date.day:
                        month[i][j] = 0
                    else:
                        break

        inline_kb = types.InlineKeyboardMarkup()

        month_name = types.InlineKeyboardButton(text=f'{month_names[r_month]} {year}', callback_data=f'day')

        inline_kb.row(month_name)
        inline_kb.row(kb_mon, kb_tue, kb_wed, kb_thu, kb_fri, kb_sat, kb_sun)
        for week in month:
            week_days = []
            for day in week:
                callback = 'day'
                if day != 0:
                    date = datetime.datetime.now()
                    minute = date.minute if date.minute % 5 == 0 else (date.minute - date.minute % 5) - 5   # makes minute value mod 5(5, 10, 15 etc)
                    callback = f'set_inline_watch:{year}-{r_month}-{day}+{date.hour}:{minute}:00_type:{what_date}_ev_id:{ev_id}'
                    # callback data which creates time picker, initialised with selected here data

                kb_day = types.InlineKeyboardButton(text=f'{day if day != 0 else "⠀"}', callback_data=callback)
                week_days.append(kb_day)
            inline_kb.row(*week_days)  # unpacks list

        prev = types.InlineKeyboardButton(text=f'{emojize(" :arrow_backward:", use_aliases=True)}',
                                          callback_data=f'show_calendar_for_date:{year}-{r_month - 1 if r_month != 1 else 12}_type_of_date:{what_date}_event_id:{ev_id}')

        next = types.InlineKeyboardButton(text=f'{emojize(" :arrow_forward:", use_aliases=True)}',
                                          callback_data=f'show_calendar_for_date:{year}-{r_month + 1 if r_month != 12 else 1}_type_of_date:{what_date}_event_id:{ev_id}')

        if prev_m and next_m:
            inline_kb.row(prev, next)
        elif not prev_m and next_m:
            inline_kb.row((next))

        return inline_kb
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('set_inline_watch:')) > 1)
def set_inline_watch_handler(call):
    try:
        type_of_date = int(call.data.split('_type:')[1].split('_')[0])
        event_id = int(call.data.split('_ev_id:')[1])
        mysql_date = f'{call.data.split("set_inline_watch:")[1].split("+")[0]}' # year-month-day

        hour = int(call.data.split('+')[1].split(':')[0])
        minute = int(call.data.split('+')[1].split(':')[1])

        msg = f'Виберіть час {"початку" if type_of_date == 0 else "закінчення"} події:'
        inline_kb = types.InlineKeyboardMarkup()

        plus_hour = types.InlineKeyboardButton(text=f'{emojize("  :arrow_up_small:", use_aliases=True)}',
                                               callback_data=f'set_inline_watch:{mysql_date}+{hour+1 if hour != 23 else 00}:{minute}:00_type:{type_of_date}_ev_id:{event_id}')
        empty = types.InlineKeyboardButton(text=f'⠀', callback_data='empty')
        plus_min = types.InlineKeyboardButton(text=f'{emojize("  :arrow_up_small:", use_aliases=True)}',
                                              callback_data=f'set_inline_watch:{mysql_date}+{hour}:{minute+5 if minute != 55 else 00}:00_type:{type_of_date}_ev_id:{event_id}')

        btn_hour = types.InlineKeyboardButton(text=f'{hour}', callback_data='empty')
        dots = types.InlineKeyboardButton(text=f':', callback_data='empty')
        btn_min = types.InlineKeyboardButton(text=f'{minute}', callback_data='empty')

        minus_hour = types.InlineKeyboardButton(text=f'{emojize(" :arrow_down_small:", use_aliases=True)}',
                                                callback_data=f'set_inline_watch:{mysql_date}+{hour-1 if hour != 00 else 23}:{minute}:00_type:{type_of_date}_ev_id:{event_id}')
        minus_min = types.InlineKeyboardButton(text=f'{emojize("  :arrow_down_small:", use_aliases=True)}',
                                               callback_data=f'set_inline_watch:{mysql_date}+{hour}:{minute-5 if minute != 00 else 55}:00_type:{type_of_date}_ev_id:{event_id}')

        inline_kb.row(plus_hour, empty, plus_min)
        inline_kb.row(btn_hour, dots, btn_min)
        inline_kb.row(minus_hour, empty, minus_min)
        inline_kb.row(empty)
        inline_kb.row(types.InlineKeyboardButton(text=f"{emojize(' :white_check_mark:', use_aliases=True)}",
                                                 callback_data=f"update_event_date:{mysql_date}+{hour}:{minute}:00_type:{type_of_date}_ev_id:{event_id}"))

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('show_calendar_for_date:')) > 1)
def show_calendar_for_date_handler(call):
    try:
        period = call.data.split('show_calendar_for_date:')[1].split('_')[0]
        year = int(period.split('-')[0])
        month = int(period.split('-')[1])
        type_of_date = int(call.data.split('type_of_date:')[1].split('_')[0])
        event_id = int(call.data.split('event_id:')[1])
        date = datetime.datetime.now()

        inline_kb = generate_calendar_keyboard(year, month, False if month == date.month else True, True, type_of_date, event_id)

        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_date:')) > 1)
def update_event_date_handler(call):
    try:
        mysql_date = call.data.split('update_event_date:')[1].split('_')[0].replace('+', ' ')
        type_of_date = int(call.data.split('_type:')[1].split('_')[0])
        ev_id = int(call.data.split('_ev_id:')[1])

        msg = f'Дані про дату {"початку" if type_of_date == 0 else "закінчення"} події оновлено!{emojize(":tada:", use_aliases=True)}'

        if not type_of_date:
            model.update_event_start_date(ev_id, mysql_date)
        else:
            date_starts = [x for x in model.get_client_events(call.message.chat.id) if x[0]==ev_id][0][4]
            date_ends = datetime.datetime.strptime(mysql_date, '%Y-%m-%d %H:%M:%S')
            if date_starts is not None:
                diff = date_ends - date_starts

                if diff.days >=0 and diff.seconds > 0:
                    model.update_event_end_date(ev_id, mysql_date)
                else:
                    msg = f'Дані про дату закінчення події не оновлено, ' \
                          f'оскільки дата закінчення аипереджає дату початку!'

        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}Назад', callback_data=f'back_to_detailed_request_event_id:{ev_id}')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_date_ends_ev_id:')) > 1)
def update_event_date_ends_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_date_ends_ev_id:')[1])

        now = datetime.datetime.now()
        date_starts = [x for x in model.get_client_events(call.message.chat.id) if x[0] == event_id][0][4]

        msg = f'Виберіть дату закінчення події:'
        inline_kb = generate_calendar_keyboard(now.year, now.month, False, True, 1, event_id)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('back_to_detailed_request_event_id:')) > 1)
def back_to_detailed_request_event_id_handler(call):
    try:
        event_id = int(call.data.split('back_to_detailed_request_event_id:')[1])
        event_request_id = [x[1] for x in model.get_client_events(call.message.chat.id) if x[0]== event_id][0]

        show_event_request_details(call.message, event_request_id, True)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_title_ev_id:')) > 1)
def update_event_title_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_title_ev_id:')[1])
        msg = f'Введіть назву події:'

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg)

        bot.register_next_step_handler_by_chat_id(call.message.chat.id, update_event_title, event_id)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def update_event_title(message, *args):
    """
    Method updates event title (without creating new event)
    :param message:message instance
    :param args:(event id)
    :return: None
    """
    try:
        event_id = args[0]
        model.update_event_title(event_id, message.text)
        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}Назад', callback_data=f'back_to_detailed_request_event_id:{event_id}')

        inline_kb.row(back)

        bot.send_message(chat_id=message.chat.id,
                              text=f'Назву події було оновлено{emojize(":tada:", use_aliases=True)}',
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_location_ev_id:')) > 1)
def update_event_location_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_location_ev_id:')[1])
        msg = f'Відправте боту локацію на якій проходитиме святкування події ' \
              f'(використовуйте тільки вбудовані засоби Telegram, якщо ви використовуєте мобільний додаток.' \
              f' В інакшому випадку залиште цей пункт не заповненим, та попросіть менеджера це зробити):'

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg)

        bot.register_next_step_handler_by_chat_id(call.message.chat.id, update_event_location, event_id)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def update_event_location(message, *args):
    try:
        event_id = args[0]
        model.update_event_location(event_id, message.location.latitude, message.location.longitude)

        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}Назад',
                                          callback_data=f'back_to_detailed_request_event_id:{event_id}')
        inline_kb.row(back)

        bot.send_message(chat_id=message.chat.id,
                         text=f'Локацію події було оновлено{emojize(":tada:", use_aliases=True)}',
                         reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_type_ev_id:')) > 1)
def update_event_type_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_type_ev_id:')[1])
        msg = f'Виберіть тип події:'
        inline_kb = types.InlineKeyboardMarkup()

        for ev_type in model.get_event_types():
            inline_kb.row(types.InlineKeyboardButton(text=f'{ev_type[1]}', callback_data=f'update_event_type_type_id:{ev_type[0]}_ev_id:{event_id}'))

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_type_type_id:')) > 1)
def update_event_type_type_id_handler(call):
    try:
        event_type_id = int(call.data.split('update_event_type_type_id:')[1].split('_')[0])
        event_id = int(call.data.split('_ev_id:')[1])

        model.update_event_type(event_id, event_type_id)

        msg = f'Тип події оновлено!{emojize(":tada:", use_aliases=True)}'
        inline_kb = types.InlineKeyboardMarkup()

        back = back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}Назад',
                                          callback_data=f'back_to_detailed_request_event_id:{event_id}')
        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_class_ev_id:')) > 1)
def update_event_class_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_class_ev_id:')[1])
        msg = f'Виберіть тип події:'
        inline_kb = types.InlineKeyboardMarkup()

        for ev_class in model.get_event_classes():
            inline_kb.row(types.InlineKeyboardButton(text=f'{ev_class[1]}', callback_data=f'update_event_class_class_id:{ev_class[0]}_ev_id:{event_id}'))

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_class_class_id:')) > 1)
def update_event_class_class_id_handler(call):
    try:
        event_class_id = int(call.data.split('update_event_class_class_id:')[1].split('_')[0])
        event_id = int(call.data.split('_ev_id:')[1])

        model.update_event_class(event_id, event_class_id)

        msg = f'Клас події оновлено!{emojize(":tada:", use_aliases=True)}'
        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}Назад',
                                                 callback_data=f'back_to_detailed_request_event_id:{event_id}')
        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('update_event_number_of_guests_ev_id:')) > 1)
def update_event_number_of_guests_ev_id_handler(call):
    try:
        event_id = int(call.data.split('update_event_number_of_guests_ev_id:')[1])
        msg = f'Введіть кількість гостей:'

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, update_event_number_of_guests, event_id)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def update_event_number_of_guests(message, *args):
    try:
        event_id = args[0]
        number_of_guests = 0
        msg = ''
        inline_kb = types.InlineKeyboardMarkup()

        try:
            number_of_guests = int(message.text)
        except ValueError as v_err:
            number_of_guests = -1

        if number_of_guests <= 0:   # if its -1 from invalid input, or user entered negative value
            msg = f'Дані не було оновлено! Перевірте правильність введених даних, це повинне бути число більше 0!'
            inline_kb.row(types.InlineKeyboardButton(text=f'{emojize("  :arrows_counterclockwise:", use_aliases=True)}Повторити',
                                                     callback_data=f'update_event_number_of_guests_ev_id:{event_id}'))
        else:
            model.update_event_number_of_guests(event_id, number_of_guests)
            msg = f'Кількість гостей оновлено!{emojize(":tada:", use_aliases=True)}'
            inline_kb.row(types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}Назад',
                                                 callback_data=f'back_to_detailed_request_event_id:{event_id}'))

        bot.send_message(chat_id=message.chat.id,
                         text=msg,
                         reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def check_if_user_entered_personal_info(func):
    """
    Decorator for function completing request registration
    :param func: function to wrap
    :return: inner wrapped function
    """
    def inner_func(call):
        event_req_id = int(call.data.split('complete_request_registration_ev_req_id:')[1])
        user = model.get_client(call.message.chat.id)

        if user[4] is None or user[6] is None:
            msg = f'Для завершення реєстрації заявки заповніть будь-ласка необхідні контактні дані, ' \
                  f'щоб менеджер міг з Вами зв\'язатись:'

            inline_kb = types.InlineKeyboardMarkup()

            get_lname = types.InlineKeyboardButton(text=f'{emojize(" :clipboard:", use_aliases=True)}Прізвище', callback_data=f'set_client_last_name_ev_req_id:{event_req_id}')
            get_number = types.InlineKeyboardButton(text=f'{emojize(" :phone:", use_aliases=True)}Номер телефону', callback_data=f'set_client_phone_number_ev_req_id:{event_req_id}')

            if user[4] is None:
                inline_kb.row(get_lname)
            if user[6] is None:
                inline_kb.row(get_number)

            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=msg,
                                  reply_markup=inline_kb)
        else:
            func(call)
    return inner_func


@bot.callback_query_handler(func=lambda call: len(call.data.split('complete_request_registration_ev_req_id:')) > 1)
@check_if_user_entered_personal_info
def complete_request_registration_ev_req_id_handler(call):
    try:
        event_req_id = int(call.data.split('complete_request_registration_ev_req_id:')[1])

        model.confirm_request_registration(event_req_id)

        msg = f'Заявку зареєстровано!{emojize(":tada:", use_aliases=True)}\nНайближчим часом з ' \
              f'вами зв\'яжеться менеджер для підтвердження або уточнення'
        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню', callback_data='main_menu')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: call.data.split('set_client_last_name_ev_req_id:').__len__() > 1 )
def set_client_last_name_handler(call):
    try:
        event_req_id = call.data.split('set_client_last_name_ev_req_id:')[1]
        msg = f'Введіть своє прізвище:'

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, set_client_last_name, event_req_id)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def set_client_last_name(message, *args):
    try:
        ev_req_id = args[0]
        model.update_client_last_name(message.chat.id, message.text)

        msg = f'Ваше прізвище оновлено!{emojize(":tada:", use_aliases=True)}'
        inline_kb = types.InlineKeyboardMarkup()

        inline_kb.row( types.InlineKeyboardButton(text=f'{emojize(" :arrow_right:", use_aliases=True)}Далі',
                                          callback_data=f'complete_request_registration_ev_req_id:{ev_req_id}'))

        bot.send_message(chat_id=message.chat.id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('set_client_phone_number_ev_req_id:')) > 1)
def set_client_phone_number_ev_req_id_handler(call):
    try:
        event_req_id = call.data.split('set_client_phone_number_ev_req_id:')[1]

        ev_req_for_contact_updating[call.message.chat.id] = event_req_id

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_phone = types.KeyboardButton(text="Відправити номер телефону", request_contact=True)
        keyboard.add(button_phone)
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(chat_id=call.message.chat.id,
                         text='Відправте будь-ласка свій номер',
                         reply_markup=keyboard)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('show_price_changes_ev_id:')) > 1)
def show_price_changes_ev_id_handler(call):
    try:
        ev_id = int(call.data.split('show_price_changes_ev_id:')[1])
        event = model.get_client_event_extended(ev_id)
        msg = f'{emojize(" :information_source:", use_aliases=True)}Ціну на вашу подію було оновлено!{emojize(" :information_source:", use_aliases=True)}\n' \
              f'{"-" * 20}\n' \
              f'{emojize(" :moneybag:", use_aliases=True)}Ціна обслуговування вашої події *{event[7]}*, ' \
              f'яка відбудеться *{event[9]}* складає *{event[15]}*грн.'

        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню', callback_data='main_menu')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              parse_mode='Markdown',
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def update_menu_to_not_relevant_data(client_id):
    """
    Edits menu message, to send new message with relevant information
    :param client_id: client telegram id
    :return: None
    """
    try:
        menu_id = model.get_client_last_message_id(client_id)
        msg = f'{emojize(" :scream:", use_aliases=True)}Дана інформація застаріла, ви отримаєте нове повідомлення з актуальною)'

        bot.edit_message_text(chat_id=client_id,
                              message_id=menu_id,
                              text=msg)
    except Exception as err:
            method_name = sys._getframe().f_code.co_name
            logger.write_to_log('exception', 'controller')
            logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('show_event_feedback_menu_ev_id:')) > 1)
def set_event_feedback_ev_id_handler(call):
    try:
        ev_id = int(call.data.split('show_event_feedback_menu_ev_id:')[1])
        event = model.get_client_event_extended(ev_id)

        msg = f'Будь ласка, оцініть нашу роботу на події *{event[7]}*, ' \
              f'яка відбувалась з {emojize(" :clock4:", use_aliases=True)}*{event[9]}* ' \
              f'по {emojize(" :clock430:", use_aliases=True)}*{event[10]}*:'

        inline_kb = types.InlineKeyboardMarkup()

        for i in range(1, 6, 1):
            inline_kb.row(types.InlineKeyboardButton(text=f'{emojize(" :star:", use_aliases=True) * i}',
                                                     callback_data=f'set_event_feedback_ev_id:{ev_id}_fb:{i}'))

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              parse_mode='Markdown',
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('set_event_feedback_ev_id:')) > 1)
def set_event_feedback_ev_id_handler(call):
    try:
        ev_id = call.data.split('set_event_feedback_ev_id:')[1].split('_')[0]
        feedback = call.data.split('_fb:')[1]

        model.update_event_feedback(ev_id, feedback)

        msg = f'Дякуємо за відгук!{emojize(" :relaxed:", use_aliases=True)}'
        inline_kb = types.InlineKeyboardMarkup()

        sock_handler.send_socket_command(f'feedback_updated-{ev_id}')

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню', callback_data='main_menu')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('events_archive_page:')) > 1)
def events_archive_handler(call):
    try:
        page = int(call.data.split('events_archive_page:')[1])
        num_of_pages, events = model.get_event_archive_page(call.message.chat.id, page)

        msg = f'Виберіть подію, про яку хочете отримати інформацію:\n' \
              f'{emojize(" :page_facing_up:", use_aliases=True)}Сторінка {page+1}/{num_of_pages}'
        inline_kb = types.InlineKeyboardMarkup()

        if num_of_pages > 0:
            for event in events:
                inline_kb.row(types.InlineKeyboardButton(text=f'{event[2]} {event[4]}',
                                                         callback_data=f'show_archive_ev_id:{event[0]}'))
            next_page_indi = False
            prev_page_indi = False

            next_page = types.InlineKeyboardButton(text=f'{emojize(" :arrow_forward:", use_aliases=True)}',
                                                   callback_data=f'events_archive_page:{page + 1}')
            prev_page = types.InlineKeyboardButton(text=f'{emojize(" :arrow_backward:", use_aliases=True)}',
                                                   callback_data=f'events_archive_page:{page - 1}')

            if page + 1 == num_of_pages:
                next_page_indi = False
            else:
                next_page_indi = True
            if page == 0:
                prev_page_indi = False
            else:
                prev_page_indi = True

            if prev_page_indi and next_page_indi:
                inline_kb.row(prev_page, next_page)
            if prev_page_indi and not next_page_indi:
                inline_kb.row(prev_page)
            if not prev_page_indi and next_page_indi:
                inline_kb.row(next_page)
        else:
            pass
        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню', callback_data='main_menu')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


@bot.callback_query_handler(func=lambda call: len(call.data.split('show_archive_ev_id:')) > 1)
def show_archive_ev_id_handler(call):
    try:
        ev_id = call.data.split('show_archive_ev_id:')[1]
        event = model.get_client_event_extended(ev_id)

        created_request_date_str = f'{emojize(" :boom:", use_aliases=True)}Заявку подано:{event[2]}'
        request_processed_str = f'{emojize(" :heavy_multiplication_x:" if event[4] != 1 else ":heavy_check_mark:", use_aliases=True)}' \
                                f'Заявку {"опрацьовано" if event[4] == 1 else "не опрацьовано"}'
        event_title_str = f'{emojize(" :boom:", use_aliases=True)}Назва події: {event[7]}'
        event_location_str = f'{emojize(" :round_pushpin:", use_aliases=True)}Місце проведення: {event[8] if event[8] is not None else "не зазначено"}'
        date_starts_str = f'{emojize(":clock4:", use_aliases=True)}Дата початку: {event[9] if event[9] is not None else "не зазначено"}'
        date_ends_str = f'{emojize(" :clock430:", use_aliases=True)}Дата закінчення: {event[10] if event[10] is not None else "не зазначено"}'
        event_type_str = f'{emojize(" :grey_question:", use_aliases=True)}Тип події: {[x[1] for x in model.get_event_types() if x[0] == event[11]][0] if event[11] is not None else "не зазначено"}'
        event_class_str = f'{emojize(" :sparkles:", use_aliases=True)}Клас події: {[x[1] for x in model.get_event_classes() if x[0] == event[12]][0] if event[12] is not None else "не зазначено"}'
        guests_str = f'{emojize(" :tophat:", use_aliases=True)}Кількість гостей: {event[13] if event[13] is not None else "не зазначено"}'

        msg = f'{emojize(" :pencil2:", use_aliases=True)} Відомості про проведену подію\n' \
              f'{"-" * 20}\n' \
              f'{created_request_date_str}\n' \
              f'{request_processed_str}\n' \
              f'{"-" * 20}\n' \
              f'{event_title_str}\n' \
              f'{event_location_str}\n' \
              f'{date_starts_str}\n' \
              f'{date_ends_str}\n' \
              f'{event_type_str}\n' \
              f'{event_class_str}\n' \
              f'{guests_str}\n'

        inline_kb = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}До меню', callback_data='main_menu')

        inline_kb.row(back)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')

# socket notifications


def notify_about_price_changes(client_id, event_id):
    """
    Handles command got from staff bot, to notify client about fact, price were changed
    :param client_id: client telegram id
    :param event_id: event id, where price were changed
    :return: None
    """
    try:
        msg = f'Ціна на одну з ваших подій змінилась! натисніть кнопку, щоб отримати інформацію'
        inline_kb = types.InlineKeyboardMarkup()

        inline_kb.row(types.InlineKeyboardButton(text=f'{emojize(" :information_source:", use_aliases=True)}',
                                                 callback_data=f'show_price_changes_ev_id:{event_id}'))
        update_menu_to_not_relevant_data(client_id)
        bot.send_message(chat_id=client_id,
                              text=msg,
                              reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


def request_feedback(client_id, event_id):
    """
    Notifies client about ended event, and feedback request
    :param client_id: client telegram id
    :param event_id: event id
    :return: None
    """
    try:
        msg = f'Одна з ваших подій щойно завершилась!{emojize(" :smiley:", use_aliases=True)} \n' \
              f'Будь-ласка, оцініть нашу роботу. Будьте максимально чесними, але пам\'ятайте, ' \
              f'що від вашого рішення залежть заробітня плата працівників' \
              f'{emojize(" :sweat_smile:", use_aliases=True)}'
        inline_kb = types.InlineKeyboardMarkup()

        inline_kb.row(types.InlineKeyboardButton(text=f'{emojize(" :sparkles:", use_aliases=True)}Виставити оцінку',
                                                 callback_data=f'show_event_feedback_menu_ev_id:{event_id}'))
        update_menu_to_not_relevant_data(client_id)
        bot.send_message(chat_id=client_id,
                         text=msg,
                         reply_markup=inline_kb)
    except Exception as err:
        method_name = sys._getframe().f_code.co_name
        logger.write_to_log('exception', 'controller')
        logger.write_to_err_log(f'exception in method {method_name} - {err}', 'controller')


# different message types handlers


@bot.message_handler(content_types=['contact'])
def get_contact_message(message):
    try:
        model.update_client_ph_number(message.chat.id, message.contact.phone_number)

        rem_markup = types.ReplyKeyboardRemove()
        ev_req_id = ev_req_for_contact_updating.pop(message.chat.id)

        bot.reply_to(message=message,
                     text=f'Ваш номер телефону оновлено!{emojize(":tada:", use_aliases=True)}',
                     reply_markup=rem_markup)

        msg = 'Тепер можна продовжити'
        inline_kb = types.InlineKeyboardMarkup()

        inline_kb.row(types.InlineKeyboardButton(text=f'{emojize(" :arrow_right:", use_aliases=True)}Далі',
                                                 callback_data=f'complete_request_registration_ev_req_id:{ev_req_id}'))

        bot.send_message(chat_id=message.chat.id,
                         text=msg,
                         reply_markup=inline_kb)
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
            bot.send_message(chat_id=message.chat.id, text=msg)

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
