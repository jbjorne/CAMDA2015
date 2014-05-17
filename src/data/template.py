"""
For processing experiment templates.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import json, hashlib

def getTemplateId(template):
    return hashlib.md5(json.dumps(template)).hexdigest()    

def compileTemplate(template):
    compiled = template.copy()
    lambdaArgs = sorted(template.keys())
    lambdaArgs.remove("example")
    lambdaArgs.remove("label")
    lambdaArgs.remove("features")
    compiled["example"] = compileTemplateOption(compiled["example"], ["con"] + lambdaArgs, "example")
    if "filter" in compiled:
        compiled["filter"] = compileTemplateOption(compiled["filter"], ["con", "example"] + lambdaArgs, "filter")
    compiled["label"] = compileTemplateOption(compiled["label"], ["con", "example"] + lambdaArgs, "label")
    compiled["features"] = compileTemplateOption(compiled["features"], ["con", "example"] + lambdaArgs, "features")
    compiled["meta"] = compileTemplateOption(compiled["meta"], ["example", "label", "features"] + lambdaArgs, "meta")
    lambdaArgs = {k:compiled[k] for k in lambdaArgs}
    return compiled, lambdaArgs

def compileTemplateOption(template, arguments, key=None):
    if template == None:
        return None
    if not isinstance(template, basestring):
        return [compileTemplateOption(x, arguments, key) for x in template]
    template = template.replace("\n", " ")
    if template[0] == "{" and template[-1] == "}": # Python-only statement
        s = "lambda " + ",".join(arguments) + ": " + template[1:-1].replace("/{", "{").replace("/}", "}")
        print "Compiled template", [key, s]
        return eval(s)
    else: # SQL statement
        template = template.replace("/{", "BRACKET_OPEN").replace("/}", "BRACKET_CLOSE")
        template = template.replace("{", "BRACKET_SPLITPARAM").replace("}", "BRACKET_SPLIT")
        splits = template.split("BRACKET_SPLIT")
        sql = ""
        parameters = []
        for split in splits:
            split = split.replace("BRACKET_OPEN", "{").replace("BRACKET_CLOSE", "}")
            if split.startswith("PARAM"):
                split = split[5:]
                if split.startswith("'") and split.endswith("'"):
                    sql += "('\" + " + split[1:-1] + " + \"')"
                else:
                    parameters.append(split)
                    sql += "?"
            else:
                sql += split
        sql = "lambda " + ",".join(arguments) + ": con.execute(\"" + sql
        if len(parameters) > 1:
            sql += "\", (" + ", ".join(parameters) + ",))"
        elif len(parameters) == 1:
            sql += "\", (" + parameters[0] + ",))"
        else:
            sql += "\")"
        print "Compiled template", [key, sql]
        return eval(sql)

def parseOptionString(string):
    if string == None:
        return {}
    # Separate key and values into a list, allowing commas within values
    splits = []
    equalSignSplits = string.split("=")
    for i in range(len(equalSignSplits)):
        if i < len(equalSignSplits) - 1: # potentially a "value,key2" structure from the middle of a string like "key1=value,key2=value2"
            splits.extend(equalSignSplits[i].rsplit(",", 1))
        else:
            splits.append(equalSignSplits[i])
    options = {}
    for key, value in zip(*[iter(splits)] * 2):
        try:
            options[key] = eval(value, globals(), {x:getattr(settings, x) for x in dir(settings)})
        except:
            options[key] = value
    return options

def parseTemplateOptions(string, options):
    if options == None:
        options = {}
    if string == None:
        return options
    for key, value in parseOptionString(string).items():
        options[key] = value
    return options
