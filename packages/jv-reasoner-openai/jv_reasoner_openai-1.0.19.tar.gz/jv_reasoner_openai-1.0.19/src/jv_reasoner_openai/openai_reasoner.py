import json
from jvcore import Reasoner, ActionDescription, ActionParameters, Communicator
from jvopenai import OpenAIConversation

from .helpers import EnumDecoder
from .instruction import instruction


class OpenAiReasoner(Reasoner):
    def __init__(self, communicator: Communicator):
        self.__conversation = OpenAIConversation()
        self.__initialised = False
        self.__communicator = communicator

    def selectSkill(self, commandsAndQueries: dict[str, ActionDescription], utterance: str) -> ActionParameters | None:
        self.__initialInstruction(commandsAndQueries)
        response = self.__conversation.getResponse(utterance) # todo ml 0 error when json is  not like the ActionParameters type
        return json.loads(response, cls=EnumDecoder) if response != 'none' else None
    
    def __initialInstruction(self, commandsAndQueries: dict[str, ActionDescription]) -> str:
        if not self.__initialised:
            instructions = instruction(commandsAndQueries)
            instructionAccepted = self.__conversation.getResponse(instructions) == '1'
            self.__initialised = True
            if not instructionAccepted:
                raise KeyError('Its wrong error and openai doesnt understand me (reasoner)') # debug this does not make sense, it will always understand

