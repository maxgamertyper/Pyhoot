from Pyhoot.Client import Client
import time

bot=Client(gamepin=str(input("gamepin: ")),name=str(input("name: ")),auth_bypass=True)

@bot.event_listener(type="question_started")
def question(data):
    bot.crash_lobby()

bot.start()
bot.join()
