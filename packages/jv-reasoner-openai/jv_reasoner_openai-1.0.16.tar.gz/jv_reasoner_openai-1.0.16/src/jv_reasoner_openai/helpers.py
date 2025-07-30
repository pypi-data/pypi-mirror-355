from jvcore.reasoner_base import ActionType


def decode_enums(obj):
    if 'actionType' in obj:
        obj['actionType'] = ActionType(obj['actionType'])  # Convert string to enum
    return obj