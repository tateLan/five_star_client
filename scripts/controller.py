import config
from model import Model
import telebot
from telebot import types


class Controller:
    def __init__(self):
        self.model = Model()
        self.bot = telebot.TeleBot(config.TOKEN)