from Pyhoot.Client import Client

bot=Client()

for listener_type in list(bot.ListeningData["types"].keys()):
  @bot.event_listener(listening_type=listener_type)
  def listen_test(data):
    print(listener_type)
