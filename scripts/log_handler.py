import config
from datetime import datetime
import telebot


def counter():
    """
    Generator needed for generating id of log files records
    :return: id of record
    """
    id = 1
    while True:
        yield id
        id += 1


class LogHandler:
    def __init__(self):
        log_path = f'{config.WORKING_DIR}/log/log'
        err_log_path = f'{config.WORKING_DIR}/log/err_log'

        self.log_file = open(log_path, 'ab')
        self.err_log_file = open(err_log_path, 'ab')

        self.log_file.write(config.INITIAL_LOG_TEXT.encode())
        self.log_file.seek(0)
        self.err_log_file.write(config.INITIAL_LOG_TEXT.encode())
        self.err_log_file.seek(0)

        self.log_counter = counter()
        self.err_counter = counter()

    def write_to_log(self, msg, user_id):
        """
        Method writes into log file
        :param msg: message needed to be written into error log
        :param user_id: id of user
        :return: None
        """
        message = self.generate_string_to_write(msg, user_id)

        self.log_file.write(message.encode())
        self.log_file.seek(0)

    def write_to_err_log(self, msg, bot, user_id='sys'):
        """
        :param msg: message needed to be written into error log
        :param bot: bot instance to notify developer about exception
        :param user_id: id of user to write to err log
        :return: None
        """
        # self.notifier.notify_about_exception(msg)

        print(f'exception {format(msg)}')
        message = self.generate_string_to_write(msg, user_id)

        self.err_log_file.write(message.encode())
        self.err_log_file.seek(0)

        self.write_to_log('exception handled', 'sys')

    def generate_string_to_write(self, msg, user_id):
        """
        Method generates string which can be fitted into log file specs
            message slot - 80 chars
            user slot - 25 chars
            date slot - 30 chars
        :param msg: message
        :param user_id: telegram user id
        :return: generated string ready to write into log
        """
        res_message = ''
        date = datetime.now()
        if type(msg) == Exception or type(msg) == telebot.apihelper.ApiException or type(msg) == AttributeError:
            msg = format(msg)
        msg_len = len(msg)
        usr_len = len(str(user_id))
        date_len = len(date.__str__())

        message_bigger_than_slot = False
        msg_offset = round(int((80 - msg_len) / 2))
        usr_offset = round(int((26 - usr_len) / 2))
        date_offset = round(int((30 - date_len) / 2))

        if msg_offset < 0:
            message_bigger_than_slot = True
            msg = [msg[i:i+78] for i in range(0, len(msg), 78)]
            msg_offset = 1

        if message_bigger_than_slot:
            res_message = f'|{next(self.log_counter)}|{msg_offset * " "}{msg[0]}{msg_offset * " "}|{usr_offset * " "}{user_id}{usr_offset * " "}|{date_offset * " "}{date}{date_offset * " "}|\n'

            for i in msg[1:-1]:
                res_message += f'| |{msg_offset * " "}{i}{msg_offset * " "}|{25 * " "}|{30 * " "}|\n'
            res_message += f'| |{msg_offset * " "}{msg[-1]}{(79-len(msg[-1])) * " "}|{25 * " "}|{30 * " "}|\n'

        else:
            res_message = f'|{next(self.log_counter)}|{msg_offset * " "}{msg}{msg_offset * " " if (msg_offset*2 + msg_len) == 80 else (msg_offset+1) * " "}|{usr_offset * " "}{user_id}{usr_offset * " "}|{date_offset * " "}{date}{date_offset * " "}|\n'

        return res_message
