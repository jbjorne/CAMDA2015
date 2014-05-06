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

def parseTemplateOptions(string, options):
    if options == None:
        options = {}
    if string == None:
        return options
    # Separate key and values into a list, allowing commas within values
    splits = []
    phase = False
    for split in string.split("="):
        if phase: # potentially a "value,key2" structure from the middle of a string like "key1=value,key2=value2"
            splits.extend(split.rsplit(",", 1))
        else:
            splits.append(split)
        phase = not phase
    for key, value in zip(*[iter(splits)] * 2):
        try:
            options[key] = eval(value, globals(), {x:getattr(settings, x) for x in dir(settings)})
        except:
            options[key] = value
    return options
