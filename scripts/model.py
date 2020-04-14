from db_handler import DBhandler
import sys


class Model:
    def __init__(self, logger):
        self.db_handler = DBhandler()
        self.logger = logger

    def is_user_registered(self, client_id):
        """
        Checks if client is registered in system
        :param client_id: client telegram id
        :return: client info if registered, false of not
        """
        try:
            res = False
            client = self.db_handler.get_client_by_id(client_id)

            res = False if client is None else client

            return res
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def register_client_name(self, client_id, username, client_name):
        """
        Registers client into system
        :param client_id: client telegram id
        :param username: client telegram username (could be None)
        :param client_name: client first name
        :return: None
        """
        try:
            if username is not None:
                self.db_handler.register_client(client_id, username, client_name)
            else:
                self.db_handler.register_client(client_id, client_name)

            self.logger.write_to_log(f'user {client_id} registered', 'model')
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')