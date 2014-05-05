def compileTemplate(template, arguments, key=None):
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

def parseTemplateOptions(string):
    if string == None:
        return None
    options = {}
    for split in string.split(","):
        split = split.strip()
        key, value = split.split("=", 1)
        try:
            options[key] = eval(value)
        except:
            options[key] = value
    return options
