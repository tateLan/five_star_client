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
            try:
                if args.__len__() == 0:
                    return func(self)
                else:
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
