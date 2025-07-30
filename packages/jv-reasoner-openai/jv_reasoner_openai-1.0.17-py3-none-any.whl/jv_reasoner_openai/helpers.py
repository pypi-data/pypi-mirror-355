from enum import Enum
from jvcore.reasoner_base import ActionType
import json


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)
    
class EnumDecoder(json.JSONDecoder):
    def __init__(self):
        return super().__init__(object_hook=self.hook)
    
    def hook(self, obj):
        if 'actionType' in obj:
            obj['actionType'] = ActionType(obj['actionType']) 
            return obj
        return obj
