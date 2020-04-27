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
            f"from event ev left join event_request er on ev.event_request_id = er.event_request_id " \
            f"where er.client_id={client_id} and ev.date_ends<'{mysql_date}';"

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