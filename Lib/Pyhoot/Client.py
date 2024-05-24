import websocket
import time
import json as JSON
import threading
from fake_useragent import UserAgent as UA
from . import Exceptions, Token
import inspect
import random
import itertools

class BaseClient():
    def __init__(self):
        #WebSocket Data
        self.WebChannels={"META_HANDSHAKE": "/meta/handshake", "META_CONNECT": "/meta/connect", "META_DISCONNECT": "/meta/disconnect", "SERVICE_CONTROLLER": "/service/controller", "SERVICE_PLAYER": "/service/player" }
        self.WS=None
        #Storage Data
        self.data = {}
        self.sent = {}
        self.web_log=[]
        self.previous_data={}
        self.msgid=0
        #Listening Data
        self.ListeningFunctions={}
        self.ListeningTypes=[]
        # TBD Data
        self.clientid=None
        self.connection_init=threading.Event()
        self.gamepin=None
        #Constant data
        self.UserAgent = UA().random
        self.msghandler=None
    
    def send(self, msg):
        try:
            self.sent=msg[0]
            msg[0]["id"]=self.msgid
            msg = JSON.dumps(msg)
            self.web_log.append(msg)
            self.WS.send(msg)
            self.msgid += 1
            return "sent"
        except Exception as e:
            self.exception_handler(Exceptions.SendingException,e)
    
    def pong(self,ack):
        packet=self.packet_factory("META_CONNECT",ext={"ack": ack, "timesync": {"tc": self.time(), "l": 0, "o": 0}})
        self.send(packet)
        return "ponged"
    
    def time(self):
        return str(round(time.time() * 1000))
    
    def kill(self):
        if self.WS:
            self.WS.close()
        for thread in threading.enumerate():
            if thread.name == "Thread-WebSocketApp":
                thread.terminate()
        return "killed"

    def close(self):
        if self.WS:
            self.WS.close()
        return "closed"

    def event_listener(self, Ltype:str):
        def custom_decorator(func):
            if not callable(func):
                self.exception_handler(Exceptions.ListenerFunctionNotCallableException,Ltype)
            parameters = inspect.signature(func).parameters
            has_parameters = any(p.kind == p.POSITIONAL_OR_KEYWORD for p in parameters.values())
            if not has_parameters:
                self.exception_handler(Exceptions.ListenerFunctionParametersException,Ltype)
            if Ltype in self.ListeningTypes:
                self.ListeningFunctions[Ltype] = func
            else:
                self.exception_handler(Exceptions.UnknownListenerException,Ltype)
        return custom_decorator

    def ListenerFunction(self,functiontype,call=False,data=None):
        if call and callable(self.ListeningFunctions.get(functiontype)):
            self.ListeningFunctions.get(functiontype)(data=data)
            return True
        return self.ListeningFunctions.get(functiontype) if functiontype in self.ListeningFunctions else None
    
    # websocket connection to kahoot's servers
    def init_connection(self, ws):
        try:
            self.WS = ws
            self.send([{"version": "1.0", "minimumVersion": "1.0", "channel": self.WebChannels["META_HANDSHAKE"], "supportedConnectionTypes": ["websocket", "long-polling", "callback-polling"], "advice": {"timeout": 60000, "interval": 0}, "ext": {"ack": True, "timesync": {"tc": self.time(), "l": 0, "o": 0}}}])
        except Exception as e:
            self.exception_handler(Exceptions.KahootInitException,e)

    # second part of the connection to kahoot
    def second_handshake(self):
        try:
            self.send([{"channel": self.WebChannels["META_CONNECT"], "connectionType": "websocket", "advice": {"timeout": 0}, "clientId": self.clientid, "ext": {"ack": 0, "timesync": {"tc": self.time(), "l": 0, "o": 0}}}])
            self.connection_init.set()
            self.ListenerFunction("handshake_2",True,True)
        except Exception as e:
            self.exception_handler(Exceptions.KahootInitException,e)
    
    def on_open(self,ws):
        self.init_connection(ws)
    
    def on_close(self,ws):
        print("Websocket Closed")

    def on_message(self,ws, message):
        self.BaseMessageHandler(message)
        
    def BaseMessageHandler(self,msg):
        msg=JSON.loads(msg)[0]
        ack=msg.get("ext",{}).get("ack")
        data=self.data.get("data",{})
        self.data=msg
        
        #wait for first handshake response / ack
        if ack is True:
            self.ListenerFunction("handshake_1",True,True)
            self.clientid=msg["clientId"]
            self.second_handshake()
        elif ack is not None: # if the client gets heartbeat respond with a pong
            self.pong(ack)
            self.ListenerFunction("heartbeat",True,ack)
            
        error = data.get("error") if data.get("error") is not None else msg.get("error")

        if error is not None and self.disconnected==False:
            reason = str(data.get("description"))
            if reason == "Duplicate name":
                self.exception_handler(Exceptions.NameTakenException,self.name)
            elif error=="402::session_unknown":
                self.exception_handler(Exceptions.UnknownSessionException,self.clientid,self.sent.get("clientId"))
            else:
                self.exception_handler(Exceptions.UnknownException,error,reason)
            
        if callable(self.msghandler):
            self.msghandler(msg)

    def exception_handler(self,exception,param1,param2=""):
        self.close()
        if param2:
            raise exception(param1,param2)
        else:
            raise exception(param1)
        
    def packet_factory(self,channel,data="",ext={}):
        packet=[{
            "channel":self.WebChannels[channel],
            "clientId":str(self.clientid),
            "data":data,
            "ext":ext,
            "connectionType": "websocket"
            }]
        if data=="":
            packet[0].pop("data")
        return packet
    
    def data_factory(self, content, type1: str, id_int: int = -1):
        data = {
            "gameid": self.gamepin,
            "host": "kahoot.it",
            "type": str(type1),
            "id": id_int,
            "content": JSON.dumps(content),
            "name": self.name
        }
        if id_int==-1:
            data.pop("id")
        return data
    
    def find_game(self,gamepin):
        return Token.Token(gamepin,self.UserAgent,check=True)
    
class Player(BaseClient):
    def __init__(self,Auth_Brute_Force:bool=False,random_text:str="Hello, I am a bot and can not answer this question",closeafterdisconnect:bool=False):
        super().__init__()
        self.token=None
        self.random_text=random_text
        self.ListeningTypes=["heartbeat","handshake_1","handshake_2","profile_updated", "disconnected", "question_started", "question_ended", "question_awaited", "quiz_started", "quiz_ended", "unknown_message","joined","auth_reset","auth_correct","auth_incorrect"]
        self.joined=threading.Event()
        self.quizuuid=None
        self.msghandler=self.MessageHandler
        #auth
        self.auth_reset=threading.Event()
        self.auth_correct=threading.Event()
        self.authbrute=Auth_Brute_Force
        #question data
        self.questionindex=0
        self.question_data=None
        #"safety"
        self.cad=closeafterdisconnect
        self.disconnected=False
        #custom storage stuff
        self.profileid=None
    
    def start(self,gamepin:str):
        self.gamepin=gamepin
        if self.token==None:
            a=Token.Token(self.gamepin,self.UserAgent)
            self.token=a["Token"]
            self.game_info=a["info"]
        try:
            ws = websocket.WebSocketApp(f'wss://kahoot.it/cometd/{self.gamepin}/{self.token}/', on_message=self.on_message, on_open=self.on_open)
            wst=threading.Thread(target=ws.run_forever)
            wst.start()
        except Exception as e:
            self.exception_handler(Exceptions.WebSocketInitException,e)
    
    def join(self,name:str,profile:str="",quizuuid=None):
        self.connection_init.wait()  # Wait for the WebSocket connection to be established

        self.quizuuid=quizuuid
        self.name = name
        
        login_data=self.data_factory({"device":{"userAgent":f"{self.UserAgent}","screen":{"width":1920,"height":1080}}},"login")
        login_packet=self.packet_factory("SERVICE_CONTROLLER",login_data)
        login_follup_data=self.data_factory(profile,"message",16)
        login_followup_packet=self.packet_factory("SERVICE_CONTROLLER",login_follup_data)
        self.send(login_packet)
        self.send(login_followup_packet)
        
        if self.authbrute:
            self.forceauth()
        
        return True
            
    def join_crash(self,name:str):
        self.connection_init.wait()  # Wait for the WebSocket connection to be established
        self.name = name
        
        login_data=self.data_factory({"device":{"userAgent":f"{self.UserAgent}","screen":{"width":1920,"height":1080}}},"login")
        login_packet=self.packet_factory("SERVICE_CONTROLLER",login_data)
        login_follup_data=self.data_factory(None,"message",16)
        login_followup_packet=self.packet_factory("SERVICE_CONTROLLER",login_follup_data)
        self.send(login_packet)
        self.send(login_followup_packet)
        
    def forceauth(self):
        time.sleep(5)
        authcodes=[(0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 2, 3, 1), (0, 3, 1, 2), (0, 3, 2, 1), (1, 0, 2, 3), (1, 0, 3, 2), (1, 2, 0, 3), (1, 2, 3, 0), (1, 3, 0, 2), (1, 3, 2, 0), (2, 0, 1, 3), (2, 0, 3, 1), (2, 1, 0, 3), (2, 1, 3, 0), (2, 3, 0, 1), (2, 3, 1, 0), (3, 0, 1, 2), (3, 0, 2, 1), (3, 1, 0, 2), (3, 1, 2, 0), (3, 2, 0, 1), (3, 2, 1, 0)]
        self.auth_reset.wait()
        for sequence in authcodes:
                if self.auth_correct.is_set():
                    break
                packet = [{
                    "channel":self.WebChannels["SERVICE_CONTROLLER"],
                    "data":
                    {"id":50,
                     "type":"message",
                     "gameid":self.gamepin,
                     "host":"kahoot.it",
                     "content":JSON.dumps({"sequence":''.join(map(str, sequence))})},
                     "clientId":str(self.clientid),
                     "ext":{}}]
                self.send(packet)
                time.sleep(.22)
        
    def profile_generator(self,avatar:str,cosmetic:str):
        avatar_map={'WHITE_BEAR': 2350,'PENGUIN': 2300,'REINDEER': 5373,'CHRISTMAS_TREE': 5374,'COOKIE': 5375,'BROWN_RAT': 1800,'GROUNDHOG': 1600,'GRAY_RAT': 4000,'MOOSE': 1500,'PUG': 1700,'DOG': 1700, 'CAT': 1750,'RABBIT': 1850,'RED_FOX': 1900,'GRAY_FOX': 1950,'BROWN_FOX': 2000,'PANDA': 2050,'FROG': 2100,'OWL': 2150,'CHICKEN': 2200,'FEATHERLESS_CHICKEN': 2250,'GOAT': 2400,'TIGER': 2500,'KOALA': 2550,'KANGAROO': 2600,'HORSE': 2650,'BRAIN': 2950,'UNICORN': 2700,'GREEN_MONSTER': 2800,'PURPLE_MONSTER': 2850,'PINK_MONSTER': 2900,'ZOMBIE': 3000,'SKELETON': 3050,'GLOBE': 2750,}
        cosmetic_map = {'PANCAKES': 3950, 'CHRISTMAS_HAT': 5372, 'MONOCLE': 1250, 'SCARF': 2750, 'WINTER_HAT': 5371, 'EAR_MUFFS': 5370, 'SNOW_GOGGLES': 4100, 'COLORED_SUNGLASSES': 4050, 'SANTA_HAT': 5368, 'BEARD': 5367, 'TREE_HAT': 5366, 'PRESENT_HAT': 5365, 'KAHOOT_HAT': 1550, 'GLOWER_HAT': 3100, 'CROWN': 3150, 'VIKING_HAT': 3200, 'GRADUATION_CAP': 3250, 'COWBOY_HAT': 3300, 'WITCH_HAT': 3350, 'HEADPHONES': 3400, 'HEARTS': 3450, 'HEART_GLASSES': 3500, 'GOGGLES': 3550, 'HARD_HAT': 5300, 'EXPLORER_HAT': 5309, 'EYEPATCH': 3600, 'POWDERED_WIG': 1300, 'ALBERT_EINSTIEN': 1350, 'HAIR': 1400, 'SUNGLASSES': 3650, 'TOP_HAT': 3700, 'KID_HAT': 3750, 'PARTY_HAT': 3800, 'FAKE_DISGUISE': 3850, 'PACIFIER': 3900, 'ICE_CREAM_CONE': 4000, 'FOOTBALL_HELMET': 4150, 'ASTRONAUT_HELMET': 4200}
        avatarid=avatar_map.get(avatar.upper())
        cosmeticid=cosmetic_map.get(cosmetic.upper())
        return {"avatar":{"type":avatarid,"item":cosmeticid}}
    
    def update_profile(self,profile):
        self.joined.wait()
        data=self.data_factory(profile,"message",46)
        packet=self.packet_factory("SERVICE_CONTROLLER",data)
        del packet[0]["connectionType"]
        del packet[0]["data"]["name"]
        self.profileid=self.msgid+1
        self.send(packet)
    
    def disconnect(self):
        self.disconnected=True
        self.send([{"id":self.msgid,"channel":self.WebChannels["META_DISCONNECT"],"clientId":str(self.clientid),"ext":{"timesync":{"tc":self.time(),"l":0,"o":0}}}])
        self.ListenerFunction("disconnected",True,{"Reason":"Player Left"})
        self.joined.clear()
        if self.cad:
            self.close()
    
    def MessageHandler(self,msg):
        data=self.data.get("data",{})
        
        if data.get("reason")=="disconnect":
            if data.get("type")=="status" and data.get("status")=="MISSING":
                return self.ListenerFunction("disconnected",True,{"Reason":"Host Left the Game"})
            else:
                return self.ListenerFunction("disconnected",True,{"Reason":data,"Report":"This is an unknown disconnect, please report this and what happened"})
        
        msgtype=data.get("type")
        msgid=msg.get("id") if msg.get("id") is None else int(msg.get("id"))
        
        if msgid==self.profileid and msg.get("successful") is True:
            return self.ListenerFunction("profile_updated",True,True)
        elif msgid==self.profileid and msg.get("successful") is False:
            return self.ListenerFunction("profile_updated",True,False)
        
        if msgtype=="loginResponse": #if its a login response
            self.joined.set()
            if data.get("description")=="Duplicate name":
                return self.ListenerFunction("joined",True,{"Error":"Duplicate name"})
            return self.ListenerFunction("joined",True,True) # call the listener joined function
        
        ListeningIds={10:"disconnected",2:"question_started",8:"question_ended",9:"quiz_started",13:"quiz_ended",53:"auth_reset",52:"auth_correct",51:"auth_incorrect"}
        id=data.get("id")
        
        if id in list(ListeningIds.keys()):
            if id==53: # if the auth is reset
                self.auth_reset.set()
                time.sleep(1)
                self.auth_reset.clear()
                return self.ListenerFunction(ListeningIds[id],True,True)
            elif id==52: # if the auth is correct
                self.auth_correct.set()
                return self.ListenerFunction(ListeningIds[id],True,True)
            elif id==51: # auth is incorrect
                return self.ListenerFunction(ListeningIds[id],True,False)
            elif id==2:
                self.questionindex=int(JSON.loads(data.get("content")).get("gameBlockIndex"))
                self.question_data=self.data
            elif id==10:
                if data.get("content")=="{\"kickCode\":1}":
                    self.ListenerFunction("disconnected",True,{"Reason":"Host Kicked Player"})
                    self.disconnected=True
                    if self.cad:
                        self.close()
                    return
            elif id==9: #quiz_started
                # beta
                return self.ListenerFunction(ListeningIds[id],True,msg)
            elif id==8: # question_ended
                # beta
                return self.ListenerFunction(ListeningIds[id],True,msg)
            elif id==13: #quiz_ended
               #beta
                return self.ListenerFunction(ListeningIds[id],True,msg)
            if id==2: #question_started
                #beta
                return self.ListenerFunction(ListeningIds[id],True,msg)
            return self.ListenerFunction(ListeningIds[id],True,msg)
            
    def question_content_factory(self,answer,lag):
        question_type=JSON.loads(self.question_data.get("data").get("content")).get("type")
        content={
            "type":question_type,
            "questionIndex":self.questionindex,
            "meta":{"lag":lag}
        }
        if question_type=="drop_pin":
            if type(answer) is dict:
                content["pin"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="jumble" or question_type=="multiple_select_poll" or question_type=="multiple_select_quiz":
            if type(answer) is list:
                content["choice"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="brainstorming" or question_type=="word_cloud" or question_type=="open_ended":
            if type(answer) is str:
                content["text"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="feedback":
            if type(answer) is str:
                content["text"]=answer
                content["textHighlightIndex"]=-1
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="slider":
            if type(answer) is int:
                content["choice"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        else:
            if JSON.loads(self.question_data.get("data").get("content")).get("layout")=="TRUE_FALSE":
                if answer=="blue" or answer==0:
                    answer=0
                elif answer=="red" or answer==1:
                    answer=1
                else:
                    self.exception_handler(Exceptions.InvalidAnswerException,answer)
            elif question_type=="quiz":
                if answer=="blue" or answer==0:
                    answer=0
                elif answer=="red" or answer==1:
                    answer=1
                elif answer=="yellow" or answer==2:
                    answer=2
                elif answer=="green" or answer==3:
                    answer=3
                else:
                    self.exception_handler(Exceptions.InvalidAnswerException,answer)
            content["choice"]=answer
        return content

    def question_packet_factory(self,answer=None,lag=None,content=None):
        if answer is not None and lag is not None:
            content=self.question_content_factory(answer,lag)
        if content is None and answer is None and lag is None:
            return "Error no answer data sent"
        packet=[{
            "id":self.msgid,
            "channel": self.WebChannels["SERVICE_CONTROLLER"],
            "data":{
                "id":45,
                "type":"message",
                "gameid":self.gamepin,
                "host":"kahoot.it",
                "content":JSON.dumps(content)
                },
            "clientId":str(self.clientid),
            "ext":{}
        }]
        return packet
    
    def answer_crash(self):
        time.sleep(random.randint(15,25)/100)
        packet=[{
            "channel": self.WebChannels["SERVICE_CONTROLLER"],
            "data":{
                "id":45,
                "type":"message",
                "gameid":self.gamepin,
                "host":"kahoot.it",
                "content":JSON.dumps(None)
                },
            "clientId":str(self.clientid),
            "ext":{}
        }]
        self.send(packet)
        return "Sent (only works when a question is present)"
    
    def submit_answer(self,answer,delay:int=0):
        lag=round(random.random() * 60 + 5) + (delay*100)
        answer=0 if answer=="red" else answer
        answer=1 if answer=="blue" else answer
        answer=2 if answer=="yellow" else answer
        answer=3 if answer=="green" else answer
        time.sleep(delay+.25)
        packet=self.question_packet_factory(answer,lag)
        self.send(packet)
        self.questionindex+=1

    def random_answer(self,delay:int=0):
        answer=None
        content_data=JSON.loads(self.question_data.get("data").get("content"))
        question_type=content_data.get("type")
        if question_type=="drop_pin":
            # x:0 is far left
            # y:0 is far up
            answer={"x":(random.randint(0,100000000))/1000000,"y":(random.randint(0,100000000))/1000000}
        elif question_type=="jumble":
            options=int(content_data.get("numberOfChoices"))
            answer=list(random.choice(list(itertools.permutations(options))))
        elif question_type=="multiple_select_poll" or question_type=="multiple_select_quiz":
            options=int(content_data.get("numberOfChoices"))
            results=[]
            for r in range(1, options+1):
                combinations_r = list(itertools.combinations(range(options), r))
                results.extend([list(comb) for comb in combinations_r])
            answer=random.choice(results)
        elif question_type=="feedback" or question_type=="brainstorming" or question_type=="word_cloud" or question_type=="open_ended":
            answer=self.random_text
        elif question_type=="slider":
            step=int(content_data.get("step"))
            min=int(content_data.get("minRange"))
            max=int(content_data.get("maxRange"))
            number=random.randint(min,max)
            number=round(number / step) * step
            answer=number+min
        else:
            if content_data.get("layout")=="TRUE_FALSE":
                answer=random.randint(0,1)
            elif question_type=="quiz":
                answer=random.randint(0,int(content_data.get("numberOfChoices"))-1)
            elif question_type=="survey":
                answer=random.randint(0,int(content_data.get("numberOfChoices"))-1)
        self.submit_answer(answer,delay)
    
    def profile_crash(self):
        self.update_profile(None)
