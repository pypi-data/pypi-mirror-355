from jvcore import Reasoner, Communicator
from jvcore.testing import TestCommunicator
from .helpers import decode_enums
from .openai_reasoner import OpenAiReasoner
import json

def getReasoner(communicator: Communicator) -> Reasoner:
    return OpenAiReasoner(communicator)

def test():
    comm = TestCommunicator()
    reasoner = getReasoner(comm)
    
    actions = None
    with open('skills.json') as f:
        actions = json.load(f, object_hook=decode_enums)
    
    comm.print(json.dumps(actions, indent=4))
    while True:
        request = comm.getTextInput('>')
        response = reasoner.selectSkill(actions, request)
        comm.print(response)
