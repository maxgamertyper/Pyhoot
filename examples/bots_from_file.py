from Pyhoot.Client import Client
import threading

gamepin = str(input("gamepin: "))
threadlist = []
bot_instances = {}

with open("names.txt", "r") as f:
    content = f.read()
    names = content.split()
    f.close()

def create(name):
    bot_instances[name] = Client(gamepin=int(gamepin), name=name)

    @bot_instances[name].event_listener(type="question_started")
    def question(data):
        bot_instances[name].random_answer()

    bot_instances[name].start()
    bot_instances[name].join()

for name in names:
    print(name)
    t = threading.Thread(target=create, args=(name,))
    t.start()
    threadlist.append(t)

for thread in threadlist:
    thread.join()
