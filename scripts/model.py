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

    def get_client_pending_requests_extended(self, client_id):
        """
        Returns client pending requests in extended form
        :param client_id: client telegram id
        :return: list of pending requests in extended form
        """
        try:
            self.logger.write_to_log('client pending requests extended requested', 'model')
            requests = self.get_client_pending_requests(client_id)
            extended_requests = []

            if len(requests) > 0:
                for request in requests:
                    extended_requests.append(self.db_handler.get_client_request_extended(request[0]))

            return extended_requests
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def create_event(self, event_title, client_id):
        """
        Creates event request and registers event instance
        :param event_title: event title(name)
        :param client_id: client telegram id
        :return: None
        """
        try:
            event_request_id = self.db_handler.create_event_request(client_id)
            self.logger.write_to_log('event request created', 'model')

            self.db_handler.create_event(event_request_id, event_title)
            self.logger.write_to_log('event instance created', 'model')
            return event_request_id
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')
    
    def update_event_start_date(self, event_id, mysql_date):
        """
        Updates event start date
        :param event_id: event id
        :param mysql_date: string with date formatted to fit mysql format
        :return: None
        """
        try:
            self.db_handler.update_event_date_starts_by_event_request_id(event_id, mysql_date)
            self.logger.write_to_log('event date only updated', 'model')
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def update_event_end_date(self, event_id, mysql_date):
        """
        Updates event end date by event id
        :param event_id: event id
        :param mysql_date: string with date formatted to fit mysql format
        :return: None
        """
        try:
            self.db_handler.update_event_date_ends_by_event_request_id(event_id, mysql_date)
            self.logger.write_to_log('event date only updated', 'model')
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def get_client_events(self, client_id):
        """
        Returns all events (including pending requests) for client
        :param client_id: client telegram id
        :return: list of events client created
        """
        try:
            events = self.db_handler.get_client_events(client_id)
            self.logger.write_to_log('client events got', 'model')
            return events
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def update_event_title(self, event_id, title):
        """
        Updates event title (without creating event)
        :param event_id: event id
        :param title: new title
        :return: None
        """
        try:
            self.db_handler.update_event_title(event_id, title)
            self.logger.write_to_log(f'event title updated', 'model')
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')

    def update_event_location(self, event_id, latitude, longitude):
        """
        Updates event location
        :param event_id: event id
        :param latitude: latitude
        :param longitude: longitude
        :return:None
        """
        try:
            self.logger.write_to_log(f'updating event {event_id} location', 'model')

            geo = f'latitude:{latitude} longitude:{longitude}'
            self.db_handler.update_event_location(event_id, geo)
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')
    
    def get_event_types(self):
        """
        Returns list of event types
        :return:list of event types
        """
        try:
            ev_types = self.db_handler.get_event_types()
            self.logger.write_to_log(f'event types got', 'model')
            return ev_types
        except Exception as err:
            method_name = sys._getframe().f_code.co_name

            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')
    
    def update_event_type(self, event_id, type_id):
        """
        Updates event type id
        :param event_id: event id
        :param type_id: event type id
        :return:None
        """
        try:
            self.db_handler.update_event_type(event_id, type_id)
            self.logger.write_to_log(f'event type updated', 'model')
        except Exception as err:
            method_name = sys._getframe().f_code.co_name
    
            self.logger.write_to_log('exception', 'model')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'model')