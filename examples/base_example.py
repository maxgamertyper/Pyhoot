from Pyhoot.Client import Client
import time

gamepin=str(input("Enter Gamepin: "))

bot=Client(gamepin, name="Max")

@bot.event_listener(type="question_started")
def question(data):
    bot.random_answer()

#more listeners in here


#bot function calls go either in listeners or after bot.start()
bot.start()
bot.join()
