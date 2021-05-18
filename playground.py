import json

with open('config.json') as json_file:
    data = json.load(json_file)
    print(type(data))
