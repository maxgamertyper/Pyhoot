class NameTakenException(Exception):
    def __init__(self,Name) -> None:
        super().__init__(f"The Name: \"{Name}\" Is Already Taken")

class WebSocketInitException(Exception):
    def __init__(self,error) -> None:
        super().__init__(f"There was an error in initializng the websocket, \"{error}\"")

class InvalidAnswerException(Exception):
    def __init__(self,answer) -> None:
        super().__init__(f"The answer \"{answer}\" is invalid for this question")

class KahootInitException(Exception):
    def __init__(self,error) -> None:
        super().__init__(f"There was an error in connecting the websocket to kahoot, \"{error}\"")

class GamePinException(Exception):
    def __init__(self,Pin) -> None:
        super().__init__(f"The Gamepin: \"{Pin}\" could not be found")

class UnknownListenerException(Exception):
    def __init__(self,type) -> None:
        super().__init__(f"The type: \"{type}\" is not a valid listener function, check the docs for valid listeners")

class ListenerFunctionException(Exception):
    def __init__(self,type) -> None:
        super().__init__(f"The listener function with the \"{type}\" type has had an error while executing")

class ListenerFunctionParametersException(Exception):
    def __init__(self,type) -> None:
        super().__init__(f"The listener function with the \"{type}\" type does not have any paramaters for an input")

class ListenerFunctionNotCallableException(Exception):
    def __init__(self,type) -> None:
        super().__init__(f"The listener function with the \"{type}\" type is not callable")

class UnknownException(Exception):
    def __init__(self,error,description) -> None:
        super().__init__(f"Please Make An Issue Reporting this Exception: \"{error}\", description: \"{description}\"")

class SendingException(Exception):
    def __init__(self,input,error) -> None:
        super().__init__(f"When sending the message: \"{input}\" and error occured, \"{error}\"")
        
class GameJoinException(Exception):
    def __init__(self,gamepin,gametype) -> None:
        super().__init__(f"When joining the game \"{gamepin}\", the gametype \"{gametype}\" was sent which is not supported")
