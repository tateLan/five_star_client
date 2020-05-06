import config
from datetime import datetime
import mysql.connector
import sys


class DBhandler():
    def __init__(self):
        """
        Method creates db connection
        :return:
        """
        self.connect = mysql.connector.connect(
            host='vps721220.ovh.net',
            user='five_star',
            passwd='qualityisma1n',
            database='five_star',
            auth_plugin='mysql_native_password'
        )
        self.curs = self.connect.cursor(buffered=True)

        self.session_time_alive = datetime.now()

        print('db connected successfully!')

    def check_session_time_alive(func):
        """
        Decorator which tracks connection timeout
        :param func: function needed to be wrapped
        :return: wrapped function
        """
        def inner_func(self, *args):
            """
            Wraps function to check connection timeout
            :param args: arguments of function
            :return: None
            """
            now = datetime.now()
            hours = (now - self.session_time_alive).seconds / 3600

            if hours >= 4.9:
                self.connect = mysql.connector.connect(
                    host='vps721220.ovh.net',
                    user='five_star',
                    passwd='qualityisma1n',
                    database='five_star',
                    auth_plugin='mysql_native_password'
                )
                self.curs = self.connect.cursor(buffered=True)
                self.session_time_alive = datetime.now()
                self.connect.commit()
            try:
                if args.__len__() == 0:
                    self.connect.commit()
                    return func(self)
                else:
                    self.connect.commit()
                    return func(self, args)
            except Exception as err:
                meth_name = sys._getframe().f_code.co_name
                raise Exception(f'database exception in method {meth_name} - {err}')
        return inner_func

    @check_session_time_alive
    def get_client_by_id(self, *args):
        client_id = args[0][0]

        q = f'select * from client ' \
            f'where client_id={client_id};'

        self.curs.execute(q)

        return self.curs.fetchone()

    @check_session_time_alive
    def register_client(self, *args):
        q = ''
        if len(args[0]) == 2:
            client_id, client_name = args[0]
            q = f"insert into client(client_id, first_name) values ('{client_id}', '{client_name}');"
        else:
            client_id, username, client_name = args[0]
            q = f"insert into client(client_id, telegram_username, first_name) " \
                f"values ('{client_id}', '@{username}', '{client_name}');"

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_client_pending_requests(self, *args):
        client_id = args[0][0]

        q = f'select * ' \
            f'from five_star.event_request ev ' \
            f'where ev.client_id={client_id} and (processed=-1 or processed=0);'

        self.curs.execute(q)
        return self.curs.fetchall()

    @check_session_time_alive
    def get_client_ended_events(self, *args):
        client_id = args[0][0]
        date = datetime.now()
        mysql_date = f'{date.year}-{date.month}-{date.day} {date.hour}:{date.minute}:00'

        q = f"select ev.event_id, ev.event_request_id, ev.title, ev.location, ev.date_starts, ev.date_ends, " \
            f"ev.event_type_id, ev.event_class_id, ev.number_of_guests, ev.staff_needed, ev.price, ev.feedback " \
            f"from (event ev left join event_request er on ev.event_request_id = er.event_request_id) left join shift sh on sh.event_id = ev.event_id " \
            f"where er.client_id={client_id} and sh.ended=1;"

        self.curs.execute(q)
        return self.curs.fetchall()

    @check_session_time_alive
    def get_client_request_extended(self, *args):
        """
        Returns extended information about event request
        :param args: (event request id)
        :return: firstly all columns from event request, than all columns from event(
        event_req_id, client_id, date_placed, processed_by, processed,
        event_id, event_req_id, title, location, starts, ends, event_type, event_class, guests, staff, price, feedback)
        """
        request_id = args[0][0]

        q = f'select * ' \
            f'from event_request er left join event e on er.event_request_id = e.event_request_id ' \
            f'where er.event_request_id={request_id};'

        self.curs.execute(q)
        return self.curs.fetchone()

    @check_session_time_alive
    def create_event_request(self, *args):
        """
        Creates new event request
        :param args: (client telegram id)
        :return: id of created event request
        """
        client_id = args[0][0]
        date = datetime.now()
        mysql_date = f'{date.year}-{date.month}-{date.day} {date.hour}:{date.minute}:00'

        q = f"insert into event_request (client_id, date_registered, processed) " \
            f"values ({client_id}, '{mysql_date}', -1);"

        self.curs.execute(q)
        self.connect.commit()

        q = f'select last_insert_id();'

        self.curs.execute(q)
        return self.curs.fetchone()[0]

    @check_session_time_alive
    def create_event(self, *args):
        """
        Creates event instance
        :param args:(event request id, event title)
        :return:None
        """
        event_request_id, event_title = args[0]

        q = f"insert into event (event_request_id, title) " \
            f"values ({event_request_id}, '{event_title}');"

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def update_event_date_starts_by_event_request_id(self, *args):
        """
        Updates event start date (date only, without time)
        :param args: (event id, mysql date)
        :return: None
        """
        ev_id, mysql_date = args[0]
        q = f"update event set date_starts='{mysql_date}' where event_id={ev_id};"
        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def update_event_date_ends_by_event_request_id(self, *args):
        """
        Updates event ends date (date only, without time)
        :param args: (event id, mysql date)
        :return: None
        """
        ev_id, mysql_date = args[0]

        q = f"update event set date_ends='{mysql_date}' where event_id={ev_id};"
        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_client_events(self, *args):
        client_id = args[0][0]

        q = f'select e.event_id, e.event_request_id, e.title, e.location, e.date_starts, e.date_ends, ' \
            f'e.event_type_id, e.event_class_id, e.number_of_guests, e.staff_needed, e.price, e.feedback ' \
            f'from event e left JOIN event_request er on e.event_request_id = er.event_request_id ' \
            f'where er.client_id={client_id};'
        self.curs.execute(q)

        return self.curs.fetchall()

    @check_session_time_alive
    def update_event_title(self, *args):
        event_id, title = args[0]

        q = f"update event set title='{title}' where event_id={event_id};"

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def update_event_location(self, *args):
        event_id, geo = args[0]

        q = f"update event set location='{geo}' where event_id={event_id};"

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_event_types(self):
        q = 'select * from event_type;'

        self.curs.execute(q)
        return self.curs.fetchall()

    @check_session_time_alive
    def update_event_type(self, *args):
        event_id, type_id = args[0]

        q = f'update event set event_type_id={type_id} where event_id={event_id};'
        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_event_classes(self):
        q = f'select * from event_class;'

        self.curs.execute(q)
        return self.curs.fetchall()

    @check_session_time_alive
    def update_event_class(self, *args):
        event_id, class_id = args[0]

        q = f'update event set event_class_id={class_id} where event_id={event_id};'

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def update_event_number_of_guests(self, *args):
        event_id, guests = args[0]

        q = f'update event set number_of_guests={guests} where event_id={event_id};'

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def confirm_request_registration(self, *args):
        ev_req_id = args[0][0]

        q = f'update event_request set processed=0 where event_request_id={ev_req_id};'

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_client(self, *args):
        client_id = args[0][0]

        q = f'select * from client where client_id={client_id};'

        self.curs.execute(q)
        return self.curs.fetchone()

    @check_session_time_alive
    def update_client_last_name(self, *args):
        client_id, last_name = args[0]

        q = f"update client set last_name='{last_name}' where client_id={client_id};"

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def update_client_ph_num(self, *args):
        client_id, ph_num = args[0]

        q = f"update client set phone='{ph_num}' where client_id={client_id};"

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def insert_client_last_message_id(self, *args):
        client_id, message_id = args[0]

        q = f'insert into client_last_message_to_edit (client_id, message_id) ' \
            f'values ({client_id}, {message_id});'

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def update_client_last_message_id(self, *args):
        client_id, message_id = args[0]

        q = f'update client_last_message_to_edit set message_id={message_id} where client_id={client_id};'

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_client_last_message_id(self, *args):
        client_id = args[0][0]

        q = f'select message_id from client_last_message_to_edit where client_id={client_id};'

        self.curs.execute(q)
        return self.curs.fetchone()

    @check_session_time_alive
    def get_client_event_extended(self, *args):
        """
        Returns all information about event (including event request)
        :param args: (event id)
        :return: firstly all columns from event request, than all columns from event(
                 event_req_id, client_id, date_placed, processed_by, processed,
                 event_id, event_req_id, title, location, starts, ends, event_type, event_class, guests, staff, price, feedback)
        """
        event_id = args[0][0]

        q = f'select * ' \
            f'from event_request er left join event e on e.event_request_id=er.event_request_id ' \
            f'where e.event_id={event_id};'

        self.curs.execute(q)
        return self.curs.fetchone()

    @check_session_time_alive
    def update_event_feedback(self, *args):
        ev_id, feedback = args[0]

        q = f'update event set feedback={feedback} where event_id={ev_id};'

        self.curs.execute(q)
        self.connect.commit()

    @check_session_time_alive
    def get_config_value(self, *args):
        key = args[0][0]

        q = f"select _value from config where _key='{key}';"

        self.curs.execute(q)

        return self.curs.fetchone()



