import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings

def compileTemplate(template, arguments, key=None):
    if not isinstance(template, basestring):
        return [compileTemplate(x, arguments, key) for x in template]
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
                parameters.append(split)
                sql += "?"
            else:
                sql += split
        sql = "lambda " + ",".join(arguments) + ": con.execute(\"" + sql + "\", (" + ", ".join(parameters) + ",))"
        print "Compiled template", [key, sql]
        return eval(sql)

def getFeatureGroups(names, source):
    groups = []
    for name in names:
        groups.append(source[name])
    return groups

def updateTemplateOptions(template, options):
    if "options" not in template:
        if options != None:
            raise Exception("Template does not support options")
        return None
    if options != None:
        for key in options:
            if key not in template["options"]:
                raise Exception("Template does not support option '" + str(key) + "'")
            template["options"][key] = options[key]
    return template["options"]

def parseTemplateOptions(string, options):
    #print dir(settings)
    if options == None:
        options = {}
    if string == None:
        return options
    for split in string.split(","):
        #print split
        split = split.strip()
        key, value = split.split("=", 1)
        #dir(settings)
        #print sys.modules["settings"]
        #print settings
        #print {x:getattr(settings, x) for x in dir(settings)}
        #print [key, value, eval(value, globals(), settings)]
        #print "TRYING", eval(value, globals(), {x:getattr(settings, x) for x in dir(settings)})
        try:
            #print "TRYING", eval(value, locals={x:getattr(settings, x) for x in dir(settings)})
            #print value, settings[value]
            options[key] = eval(value, globals(), {x:getattr(settings, x) for x in dir(settings)})
        except:
            options[key] = value
    return options
