from Pyhoot.Client import Client
import threading
import time
import random

gamepin = str(input("gamepin: "))
threadlist = []
bot_instances = {}

with open("names.txt", "r") as f:
    content = f.read()
    names = content.split()
    f.close()

index=0
for name in names:
    names.pop(index)
    if name in names:
        names.remove(name)
    names.append(name)
    index+=1

def create(name):
    bot_instances[name] = Client(gamepin=int(gamepin), name=name)

    @bot_instances[name].event_listener(type="question_started")
    def question(data):
        time.sleep(random.randint(50,75)/100)
        bot_instances[name].random_answer()

    bot_instances[name].start()
    bot_instances[name].join()

for name in names:
    print(name)
    t = threading.Thread(target=create, args=(name,))
    t.start()
    threadlist.append(t)
    time.sleep(random.randint(10,20)/10)

for thread in threadlist:
    thread.join()
