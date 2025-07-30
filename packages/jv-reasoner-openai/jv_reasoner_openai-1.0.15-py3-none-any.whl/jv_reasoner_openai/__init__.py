from jvcore import Reasoner, Communicator, ActionType
from jvcore.testing import TestCommunicator
from .openai_reasoner import OpenAiReasoner
import json

def getReasoner(communicator: Communicator) -> Reasoner:
    return OpenAiReasoner(communicator)

def test():
    comm = TestCommunicator()
    reasoner = getReasoner(comm)
    
    actions = None
    with open('skills.json') as f:
        actions = json.load(f, object_hook=__decode_enums)
    
    comm.print(actions)
    while True:
        request = comm.getTextInput('>')
        response = reasoner.selectSkill(actions, request)
        comm.print(response)
        
def __decode_enums(obj):
    if 'actionType' in obj:
        obj['actionType'] = ActionType(obj['actionType'])  # Convert string to enum
    return obj
