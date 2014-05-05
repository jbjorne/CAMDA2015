def compileTemplate(template, arguments, key=None):
    template = template.replace("/{", "BRACKET_OPEN").replace("/}", "BRACKET_CLOSE")
    s = "\"" + template.replace("{","\" + ").replace("}"," + \"") + "\""
    if template[0] != "{" and template[-1] != "}":
        s = "con.execute(" + s + ")"
    template = template.replace("BRACKET_OPEN", "{").replace("BRACKET_CLOSE", "}")
    s = s.replace("\"\" + ", "").replace(" + \"\"", "")
    s = "lambda " + ",".join(arguments) + ": " + s
    print "Compiled template", [key, s]
    return eval(s)

def updateTemplateOptions(template, options):
    if "options" not in template:
        return None
    if options == None:
        return
    for key in options:
        template["options"][key] = options[key]

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
