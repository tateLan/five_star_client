import controller
import socket
import sys
import _thread


class SocketHandler():
    def __init__(self, model):
        try:
            self.port = 1512
            self.packet_size = 2048

            self.sock = socket.socket()
            self.sock.connect(('localhost', self.port))
            print(f'connected to socket server')
            _thread.start_new_thread(self.check_incoming_commands, ())

            self.model = model
            self.logger = model.logger
        except KeyboardInterrupt:
            self.sock.close()
            exit(0)
        except ConnectionRefusedError:
            print('socket isn\'t connected: connection refused')

    def check_incoming_commands(self):
        """
        Checks for incoming commands from socket server
        :return: None
        """
        try:
            while True:
                data = self.sock.recv(self.packet_size)
                if data.decode() == '':
                    self.sock.close()
                    print('socket closed')
                    break
                else:
                    self.classify_command(data.decode().replace('\n', ''))
        except Exception as err:
            method_name = sys._getframe().f_code.co_name
            self.logger.write_to_log('exception', 'controller')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'socket handler')

    def classify_command(self, msg):
        """
        Classifies command got from socket
        :param msg: data received from socket
        :return: None
        """
        try:
            msg = msg.split('-')

            if msg[0] == 'price_changed':
                controller.notify_about_price_changes(msg[1], msg[2])
            elif msg[0] == 'request_feedback':
                pass
            # TODO: add some cross-bot interacting commands
        except Exception as err:
            method_name = sys._getframe().f_code.co_name
            self.logger.write_to_log('exception', 'controller')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'socket handler')

    def send_socket_command(self, msg):
        """
        Sends command to another bot via socket server
        :param msg:command to pass
        :return: None
        """
        try:
            self.sock.send(msg.encode())
            self.logger.write_to_log('socket message sent', 'socket handler')
        except Exception as err:
            method_name = sys._getframe().f_code.co_name
            self.logger.write_to_log('exception', 'controller')
            self.logger.write_to_err_log(f'exception in method {method_name} - {err}', 'socket handler')



