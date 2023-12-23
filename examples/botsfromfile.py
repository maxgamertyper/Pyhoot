from Pyhoot.Client import Client
import time
import threading

botlist = []
gamepin=int(input("gamepin: "))
with open("names.txt","r") as f:
  content=f.read()
  f.close()

for i in content.split():
   botlist.append(Client(gamepin=gamepin, name = i))

def initBot():
  for i in botlist:
      i.start()
      i.join()

def answerBot():
  for i in range(0,len(botlist)):
      @botlist[i].event_listener("question_started")
      def question(data):
          for i in botlist:
              i.random_answer()


thread1 = threading.Thread(target=initBot)
thread2 = threading.Thread(target=answerBot)
thread1.start()
thread2.start()
