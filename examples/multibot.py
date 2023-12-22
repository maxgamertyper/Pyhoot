from Pyhoot.Client import Client
import time

gamepin=str(input("Enter Gamepin: "))

bot=Client(gamepin, name="Max")
bot2=Client(gamepin,name="Max2")

@bot.event_listener(type="question_started")
def question(data):
    bot.random_answer()

@bot2.event_listener(type="question_started")
def question(data):
    bot2.random_answer()

bot.start()
bot2.start()
bot.join()
bot2.join()
