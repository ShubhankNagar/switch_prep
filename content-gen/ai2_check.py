import sys, importlib, re
for name in sys.argv[1:]:
    m = importlib.import_module(name).MODULE
    for l in m["lessons"]:
        w = len(re.findall(r"\S+", l["content"]))
        print(f'{l["id"]:40s} {w:5d} words  {"python" in l["content"]}')
