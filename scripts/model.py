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

    def get_client_pending_requests(self, client_id):
        """
        Returns all not approved client requests
        :param client_id: client telegram id
        :return: list of pending requests
        """
        try:
            self.logger.write_to_log('client pending event requests requested', 'model')
            res = self.db_handler.get_client_pending_requests(client_id)
            return res if res is not None else []
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def get_client_ended_events(self, client_id):
        """
        Returns client ended events by client id
        :param client_id: client telegram id
        :return: list with ended events
        """
        try:
            self.logger.write_to_log('client ended events requested', 'model')
            res = self.db_handler.get_client_ended_events(client_id)
            return res if res is not None else []
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def get_events_without_feedback(self, client_id):
        """
        Returns events without client's feedback
        :param client_id: client telegram id
        :return: list of event, without feedback
        """
        try:
            self.logger.write_to_log('events without feedback requested', 'model')

            ended_events = self.get_client_ended_events(client_id)
            res = []

            for event in ended_events:
                if event[-1] is None:
                    res.append(event)

            return res
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')