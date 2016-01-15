def splitOptions(optionString, allowedValues=None, delimiter=","):
    actions = [x.strip() for x in optionString.split(delimiter)]
    if allowedValues:
        for action in actions:
            assert action in allowedValues
    return actions