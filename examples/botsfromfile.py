from Pyhoot.Client import Client
import threading

botlist = []
gamepin=int(input("gamepin: "))
with open("names.txt","r") as f:
  content=f.read()
  f.close()

for name in content.split():
   botlist.append(Client(gamepin=gamepin, name = name))

for bot in botlist:
    @bot.event_listener("question_started")
    def question(data):
       bot.random_answer()

def initBot():
    for bot in botlist:
        bot.start()
        bot.join()


thread1 = threading.Thread(target=initBot)
thread1.start()

thread1.join()

# warning this takes a while to initiate all the bots, might want to make multiple threads to starting at each end depending on file length
