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
        self.name=None
        #Constant data
        self.UserAgent = UA().random
        self.msghandler=None
    
    def Send(self, msg):
        try:
            self.sent=msg[0]
            msg[0]["id"]=self.msgid
            msg = JSON.dumps(msg)
            self.web_log.append(msg)
            self.WS.send(msg)
            self.msgid += 1
            return "sent"
        except Exception as e:
            self.ExceptionHandler(exception=Exceptions.SendingException,param1=e)
    
    def Pong(self,ack):
        packet=self.PacketFactory("META_CONNECT",ext={"ack": ack, "timesync": {"tc": self.Time(), "l": 0, "o": 0}})
        self.Send(packet)
        return "ponged"
    
    def Time(self):
        return str(round(time.time() * 1000))
    
    def Kill(self):
        if self.WS:
            self.WS.close()
        for thread in threading.enumerate():
            if thread.name == "Thread-WebSocketApp":
                thread.terminate()
        return "killed"

    def Close(self):
        if self.WS:
            self.WS.close()
        return "closed"

    def EventListener(self, Ltype:str):
        def custom_decorator(func):
            if not callable(func):
                self.ExceptionHandler(Exceptions.ListenerFunctionNotCallableException,Ltype)
            parameters = inspect.signature(func).parameters
            has_parameters = any(p.kind == p.POSITIONAL_OR_KEYWORD for p in parameters.values())
            if not has_parameters:
                self.ExceptionHandler(Exceptions.ListenerFunctionParametersException,Ltype)
            if Ltype in self.ListeningTypes:
                self.ListeningFunctions[Ltype] = func
            else:
                self.ExceptionHandler(Exceptions.UnknownListenerException,Ltype)
        return custom_decorator

    def ListenerFunction(self,functiontype,call=False,data=None):
        if call and callable(self.ListeningFunctions.get(functiontype)):
            self.ListeningFunctions.get(functiontype)(data=data)
            return True
        return self.ListeningFunctions.get(functiontype) if functiontype in self.ListeningFunctions else None
    
    # websocket connection to kahoot's servers
    def InitConnection(self, ws):
        try:
            self.WS = ws
            self.Send([{"version": "1.0", "minimumVersion": "1.0", "channel": self.WebChannels["META_HANDSHAKE"], "supportedConnectionTypes": ["websocket", "long-polling", "callback-polling"], "advice": {"timeout": 60000, "interval": 0}, "ext": {"ack": True, "timesync": {"tc": self.Time(), "l": 0, "o": 0}}}])
        except Exception as e:
            self.ExceptionHandler(Exceptions.KahootInitException,e)

    # second part of the connection to kahoot
    def SecondHandshake(self):
        try:
            self.Send([{"channel": self.WebChannels["META_CONNECT"], "connectionType": "websocket", "advice": {"timeout": 0}, "clientId": self.clientid, "ext": {"ack": 0, "timesync": {"tc": self.Time(), "l": 0, "o": 0}}}])
            self.connection_init.set()
            self.ListenerFunction("handshake_2",True,True)
        except Exception as e:
            self.ExceptionHandler(Exceptions.KahootInitException,e)
    
    def on_open(self,ws):
        self.InitConnection(ws)

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
            self.SecondHandshake()
        elif ack is not None: # if the client gets Heartbeat respond with a pong
            self.Pong(ack)
            self.ListenerFunction("Heartbeat",True,ack)
            
        error = data.get("error") if data.get("error") is not None else msg.get("error")

        if error is not None and self.disconnected==False:
            reason = str(data.get("description"))
            if reason == "Duplicate name":
                self.ExceptionHandler(Exceptions.NameTakenException,self.name)
            else:
                self.ExceptionHandler(Exceptions.UnknownException,error,reason)
            
        if callable(self.msghandler):
            self.msghandler(msg)

    def ExceptionHandler(self,exception,param1,param2=""):
        self.Close()
        if param2:
            raise exception(param1,param2)
        else:
            raise exception(param1)
        
    def PacketFactory(self,channel,data="",ext={}):
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
    
    def DataFactory(self, content, type1: str, id_int: int = -1):
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
    
    def FindGame(self,gamepin):
        return Token.Token(gamepin,self.UserAgent,check=True)
    
class Player(BaseClient):
    def __init__(self,Auth_Brute_Force:bool=False,random_text:str="Hello, I am a bot and can not answer this question",closeafterdisconnect:bool=False):
        super().__init__()
        self.token=None
        self.random_text=random_text
        self.ListeningTypes=["Heartbeat","Handshake1","Handshake2","ProfileUpdated", "Disconnected", "QuestionStarted", "QuestionEnded", "QuizStarted", "QuizEnded", "UnknownMessage","Joined","AuthReset","AuthCorrect","AuthIncorrect","AuthLogin","BrainstormVoting"]
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
        self.BrainstormCandidates=None
        #"safety"
        self.cad=closeafterdisconnect
        self.disconnected=False
        # quiz data
        self.quizdata=None
        #custom storage stuff
        self.profileid=None
        self.stableid=None
        self.baseavatar=None
    
    def Start(self,gamepin:str):
        self.gamepin=gamepin
        if self.token==None:
            a=Token.Token(self.gamepin,self.UserAgent)
            self.token=a["Token"]
            self.quizdata=a["info"]
        try:
            ws = websocket.WebSocketApp(f'wss://kahoot.it/cometd/{self.gamepin}/{self.token}/', on_message=self.on_message, on_open=self.on_open)
            wst=threading.Thread(target=ws.run_forever)
            wst.start()
        except Exception as e:
            self.ExceptionHandler(Exceptions.WebSocketInitException,e)
    
    def Join(self,name:str,profile:str="",quizuuid=None):
        self.connection_init.wait()  # Wait for the WebSocket connection to be established

        self.quizuuid=quizuuid
        self.name = name
        
        login_data=self.DataFactory({"device":{"userAgent":f"{self.UserAgent}","screen":{"width":1920,"height":1080}}},"login")
        login_packet=self.PacketFactory("SERVICE_CONTROLLER",login_data)
        login_follup_data=self.DataFactory(profile,"message",16)
        login_followup_packet=self.PacketFactory("SERVICE_CONTROLLER",login_follup_data)
        self.Send(login_packet)
        self.Send(login_followup_packet)
        
        if self.authbrute and self.quizdata.get("twoFactorAuth"):
            self.BruteAuth()
        
        return True
            
    def JoinCrash(self,name:str):
        self.connection_init.wait()  # Wait for the WebSocket connection to be established
        self.name = name
        
        login_data=self.DataFactory({"device":{"userAgent":f"{self.UserAgent}","screen":{"width":1920,"height":1080}}},"login")
        login_packet=self.PacketFactory("SERVICE_CONTROLLER",login_data)
        login_follup_data=self.DataFactory(None,"message",16)
        login_followup_packet=self.PacketFactory("SERVICE_CONTROLLER",login_follup_data)
        self.Send(login_packet)
        self.Send(login_followup_packet)
        
    def BruteAuth(self):
        authcodes=list(itertools.permutations([0,1,2,3],4))
        self.auth_reset.wait()
        for sequence in authcodes:
            if self.auth_correct.is_set():
                break
            self.AnswerAuth(sequence)
            time.sleep(random.randint(10,15)/100)
    
    def AnswerAuth(self,sequence):
        packet = [{
                "id":self.msgid,
                "channel":self.WebChannels["SERVICE_CONTROLLER"],
                "data":
                {"id":50,
                "type":"message",
                "gameid":self.gamepin,
                "host":"kahoot.it",
                "content":JSON.dumps({"sequence":list(sequence)})},
                "clientId":str(self.clientid),
                "ext":{}}]
        self.Send(packet)
        
    def GenerateProfile(self,avatar:str,cosmetic:str):
        avatar_map = {'POLAR_BEAR': 2350, 'PENGUIN': 2300, 'SNOWMAN': 5380, 'WOODCHUCK': 1600, 'MOOSE': 1500, 'DOG': 1700, 'CAT': 1750, 'MOUSE': 1800, 'RABBIT': 1850, 'FOX': 1900, 'WOLF': 1950, 'RACCOON': 2000, 'PANDA': 2050, 'FROG': 2100, 'OWL': 2150, 'CHICKEN': 2200, 'TURKEY': 2250, 'CAMEL': 2400, 'TIGER': 2500, 'KOALA': 2550, 'KANGAROO': 2600, 'HORSE': 2650, 'UNICORN': 2700, 'DRAGON': 2800, 'MONSTER': 2850, 'FAUN': 2900, 'BRAIN': 2950, 'ZOMBIE': 3000, 'SKELETON': 3050, 'PLANET_EARTH': 2750}
        cosmetic_map = {'PROPELLER_HAT': 3750, 'PARTY_HAT': 3800, 'DISGUISE': 3850, 'PACIFIER': 3900, 'PANCAKES': 3950, 'ICE_CREAM': 4000, 'FOOTBALL_HELMET': 4150, 'ASTRONAUT_HELMET': 4200, 'WINTER_HUNTING_HAT': 5378, 'REINDEER_HAT': 5377, 'ORANGE_HAT': 5376, 'SNOWFLAKE_HAT': 5370, 'EAR_MUFFS': 5369, '2024_GLASSES': 5379, 'DRAGON_MASK': 5402, 'REFLECTIVE_GOGGLES': 4100, 'COLORFUL_SUNGLASSES': 4050, 'SCARF': 5371, 'KAHOOT_HAT': 1550, 'FLOWER_HAT': 3100, 'CROWN': 3150, 'VIKING_HELMET': 3200, 'GRADUATION_CAP': 3250, 'COWBOY_HAT': 3300, 'WITCH_HAT': 3350, 'HEADPHONES': 3400, 'HEARTS': 3450, 'HEART_SUNGLASSES': 3500, 'GOGGLES': 3550, 'HARD_HAT': 5300, 'SAFARI_HAT': 5309, 'EYEPATCH': 3600, 'MONOCOLE': 1250, 'POWDERED_WIG': 1300, 'EINSTEIN_WIG': 1350, 'HAIR': 1400, 'SUNGLASSES': 3650, 'TOP_HAT': 3700}
        avatarid=avatar_map.get(avatar.replace(" ","_").upper())
        cosmeticid=cosmetic_map.get(cosmetic.replace(" ","_").upper())
        return {"avatar":{"type":avatarid,"item":cosmeticid}}
    
    def UpdateProfile(self,profile):
        self.joined.wait()
        data=self.DataFactory(profile,"message",46)
        packet=self.PacketFactory("SERVICE_CONTROLLER",data)
        del packet[0]["connectionType"]
        del packet[0]["data"]["name"]
        self.profileid=self.msgid+1
        self.Send(packet)
    
    def Disconnect(self):
        self.disconnected=True
        self.Send([{"id":self.msgid,"channel":self.WebChannels["META_DISCONNECT"],"clientId":str(self.clientid),"ext":{"timesync":{"tc":self.Time(),"l":0,"o":0}}}])
        self.ListenerFunction("Disconnected",True,{"Reason":"Player Left"})
        self.joined.clear()
        if self.cad:
            self.Close()
    
    def MessageHandler(self,msg):
        data=self.data.get("data",{})
        
        if data.get("reason")=="disconnect":
            if data.get("type")=="status" and data.get("status")=="MISSING":
                return self.ListenerFunction("Disconnected",True,{"Reason":"Host Left the Game"})
            else:
                return self.ListenerFunction("Disconnected",True,{"Reason":data,"Report":"This is an unknown disconnect, please report this and what happened"})
        
        if data.get("status")=="LOCKED":
            return self.ListenerFunction("Joined",True,{"Error":"Game Locked"})
        
        msgtype=data.get("type")
        msgid=msg.get("id") if msg.get("id") is None else int(msg.get("id"))
        
        if msgid==self.profileid and msg.get("successful") is True:
            return self.ListenerFunction("ProfileUpdated",True,True)
        elif msgid==self.profileid and msg.get("successful") is False:
            return self.ListenerFunction("ProfileUpdated",True,False)
        
        if msgtype=="loginResponse": #if its a login response
            self.joined.set()
            if data.get("description")=="Duplicate name":
                return self.ListenerFunction("Joined",True,{"Error":"Duplicate name"})
            return self.ListenerFunction("Joined",True,True) # call the listener Joined function
        
        ListeningIds={10:"Disconnected",2:"QuestionStarted",8:"QuestionEnded",9:"QuizStarted",13:"QuizEnded",53:"AuthReset",52:"AuthCorrect",51:"AuthIncorrect",41:"BrainstormVoting",17:"AuthLogin"}
        id=data.get("id")
        
        if id in list(ListeningIds.keys()):
            info=JSON.loads(msg.get("data").get("content"))
            if id==53: # if the auth is reset
                self.auth_reset.set()
                time.sleep(1)
                self.auth_reset.clear()
                return self.ListenerFunction(ListeningIds[id],True,True)
            elif id==52: # if the auth is correct
                self.auth_correct.set()
                followuppacket=[{
                "id":self.msgid,
                "channel":self.WebChannels["SERVICE_CONTROLLER"],
                "data":
                    {"gameid":self.gamepin,
                    "type":"message",
                    "host":"kahoot.it",
                    "id":16,
                    "content":JSON.dumps(
                        {"stableIdentifier":self.stableid,
                        "usingNamerator": self.quizdata.get("namerator"),
                        "avatar": self.baseavatar
                        })
                    },
                "clientId":self.clientid,
                "ext":{}}]
                self.Send(followuppacket)
            elif id==51: # auth is incorrect
                return self.ListenerFunction(ListeningIds[id],True,False)
            elif id==10: # disconnected
                if info.get("kickCode")==1:
                    self.ListenerFunction(ListeningIds[id],True,{"Reason":"Host Kicked Player"})
                    self.disconnected=True
                    if self.cad:
                        self.Close()
                    return
            elif id==9: #QuizStarted
                upcomingqdata=info.get("upcomingGameBlockData")
                return_data={
                    "QuestionCount":info.get("gameBlockCount"),
                }
                for i,v in enumerate(upcomingqdata):
                    PointType= "Double" if v.get("pointsMultiplier")==2 else "Standard" if v.get("pointsMultiplier")==1 else "None"
                    QuestionType=v.get("type") if v.get("layout") not in ["TRUE_FALSE","MEDIA_BIG_TITLE"] else "True or False" if v.get("layout")=="TRUE_FALSE" else "Slide"
                    if i==0:
                        return_data["UpcomingQuestionData"]={
                            "type":QuestionType,
                            "PointType": PointType,
                            "media": v.get("media")
                        }
                    else:
                        return_data[f"Question{i}"]={
                            "type":QuestionType,
                            "PointType": PointType,
                        }
                return self.ListenerFunction(ListeningIds[id],True,return_data)
            elif id==13: #QuizEnded
                return_data={
                    "Rank": info.get("rank"),
                    "MedalType": info.get("podiumMedalType"),
                    "QuizName": info.get("quizTitle"),
                    "QuizId": info.get("quizId"),
                    "IsNonPointQuiz": info.get("isOnlyNonPointGameBlockKahoot"),
                    "OrganizationId": info.get("organisationId"),
                    "PrimaryUsage": info.get("primaryUsage"),
                    "QuizCoverData":{
                        "QuizCoverAltText": info.get("coverMetadata").get("altText"),
                        "QuizCoverType": info.get("coverMetadata").get("contentType"),
                        "QuizCoverOrigin": info.get("coverMetadata").get("origin"),
                        "QuizCoverSize": (info.get("coverMetadata").get("width"),info.get("coverMetadata").get("height"))
                    },
                    "PlayerStatistics": {
                        "IncorrectAnswers": info.get("incorrectCount"),
                        "CorrectAnswers": info.get("correctCount"),
                        "TotalScore": info.get("totalScore")
                    }
                }
                return self.ListenerFunction(ListeningIds[id],True,return_data)
            elif id==2: #QuestionStarted
                self.questionindex=int(JSON.loads(data.get("content")).get("gameBlockIndex"))
                self.question_data=self.data
                questiontype=info.get("type")
                return_data={
                    "QuestionType": info.get("type") if info.get("layout") not in ["TRUE_FALSE","MEDIA_BIG_TITLE"] else "True or False" if info.get("layout")=="TRUE_FALSE" else "Slide",
                    "QuestionNumber": info.get("gameBlockIndex"),
                    "QuizQuestionCount": info.get("totalGameBlockCount"),
                    "QuestionTime": info.get("timeAvailable"),
                    "NumberOfChoices": info.get("numberOfChoices"),
                    "SliderData": None if questiontype != "slider" else {
                        "Unit": info.get("unit"),
                        "Minimum": info.get("minRange"),
                        "Maximum": info.get("maxRange"),
                        "Step": info.get("step")
                    },
                    "BrainstormData": None if questiontype != "brainstorming" else {
                    "NumberOfAnswers": info.get("numberOfAnswersAllowed"),
                    "MaximumAnswerLength": info.get("allowedCharacterLengthPerAnswer")
                    },
                    "DropPinData": None if questiontype != "drop_pin" else {
                        "VideoData": info.get("video"),
                        "ImageURL": info.get("image"),
                        "ImageData": info.get("imageMetadata"),
                        "Media": info.get("media")
                    }
                }
                return self.ListenerFunction(ListeningIds[id],True,return_data)
            elif id==8: # QuestionEnded
                return_data={
                    "Correct": info.get("isCorrect"),
                    "CorrectAnswer": info.get("correctChoices"),
                    "LeaderboardRank": info.get("rank"),
                    "LeaderboardScore": info.get("totalScore"),
                    "PointsData":{
                        "PointsWithBonuses": info.get("pointsData").get("totalPointsWithBonuses"),
                        "QuestionPoints": info.get("pointsData").get("questionPoints")
                    },
                    "AnswerStreak": info.get("pointsData").get("answerStreakPoints").get("streakLevel"),
                    "EndedQuestion": int(info.get("pointsData").get("lastGameBlockIndex"))+1,
                    "NemesisData": None if "nemesis" not in info else {
                        "NemesisName": info.get("nemesis").get("name"),
                        "NemesisScore": info.get("nemesis").get("totalScore"),
                    }
                }
                return self.ListenerFunction(ListeningIds[id],True,return_data)
            elif id==41: # Brainstorm Voting Started
                candidates=info.get("candidates")
                self.BrainstormCandidates=candidates
                return self.ListenerFunction(ListeningIds[id],True,{"Candidates":candidates})
            elif id==17: #AuthLogin
                if info.get("loginState")==0:
                    self.stableid=info.get("stableIdentifier")
                    self.baseavatar=info.get("avatar")
                    return
                elif info.get("loginState")==3:
                    return self.ListenerFunction(ListeningIds[id],True,True)
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
                self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="jumble" or question_type=="multiple_select_poll" or question_type=="multiple_select_quiz":
            if type(answer) is list:
                content["choice"]=answer
            else:
                self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="brainstorming" or question_type=="word_cloud" or question_type=="open_ended":
            if type(answer) is str:
                content["text"]=answer
            else:
                self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="feedback":
            if type(answer) is str:
                content["text"]=answer
                content["textHighlightIndex"]=-1
            else:
                self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="slider":
            if type(answer) is int:
                content["choice"]=answer
            else:
                self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
        else:
            if JSON.loads(self.question_data.get("data").get("content")).get("layout")=="TRUE_FALSE":
                if answer=="blue" or answer==0:
                    answer=0
                elif answer=="red" or answer==1:
                    answer=1
                else:
                    self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
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
                    self.ExceptionHandler(Exceptions.InvalidAnswerException,answer)
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
    
    def AnswerCrash(self):
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
        self.Send(packet)
        return "Sent (only works when a question is present)"
    
    def SubmitAnswer(self,answer,delay:int=0):
        answer=0 if answer=="red" else answer
        answer=1 if answer=="blue" else answer
        answer=2 if answer=="yellow" else answer
        answer=3 if answer=="green" else answer
        time.sleep(delay+.25)
        packet=self.question_packet_factory(answer,delay)
        self.Send(packet)
        self.questionindex+=1

    def RandomAnswer(self,delay:int=0):
        answer=None
        content_data=JSON.loads(self.question_data.get("data").get("content"))
        question_type=content_data.get("type")
        if question_type=="drop_pin":
            # x:0 is far left
            # y:0 is far up
            answer={"x":(random.randint(0,100000000))/1000000,"y":(random.randint(0,100000000))/1000000}
        elif question_type=="jumble":
            options=int(content_data.get("numberOfChoices"))
            answer=list(random.choice(list(itertools.permutations([i for i in range(options)]))))
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
        self.SubmitAnswer(answer,delay)
    
    def ProfileCrash(self):
        self.UpdateProfile(None)
        
    def FinishBrainstorming(self):
        finishbrainstorm_packet=[{
        "channel":self.WebChannels["SERVICE_CONTROLLER"],
        "data":{
            "gameid":self.gamepin,
            "type":"message",
            "host":"kahoot.it",
            "id":92,
            "content":"{\"areAnswersSubmitted\":true}"
            },
        "clientId":self.clientid,
        "ext":{}
        }]
        self.Send(finishbrainstorm_packet)
        
    def BrainstormVote(self,vote:bool,OptionID:int):
        BrainstormVote=[{
            "channel":self.WebChannels["SERVICE_CONTROLLER"],
            "data":{
                "gameid":self.gamepin,
                "type":"message",
                "host":"kahoot.it",
                "id":42,
                "content":JSON.dumps({"opinion":1 if vote is True else 0,"groupId":OptionID})},
            "clientId":self.clientid,
            "ext":{}
            }]
        self.Send(BrainstormVote)
    
    def RandomBrainstormVote(self,delay:int=.5):
        votes=[]
        for i in self.BrainstormCandidates:
            vote=random.choice([True,False])
            self.BrainstormVote(vote,i["id"])
            i["vote"]=vote
            votes.append(i)
            time.sleep(delay)
        return votes
