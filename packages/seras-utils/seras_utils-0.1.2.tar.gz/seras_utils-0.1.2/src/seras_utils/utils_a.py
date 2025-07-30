
import json



# def json_to_prompt(data):
#     h_level = 1
#     def parse_object(obj, h_level):
#         if type(obj) is dict:
#             l = []
#             for k, v in obj.items():
#                 if type(v) in [list, dict]:
#                     l.append(
#                         [
#                             '\t'*(h_level-1)+f'{k}:',
#                             parse_object(v, h_level+1)
#                         ]
#                     )
#                 if type(v) in [str, float, int, type(None)]:
#                     l.append(
#                         [
#                             f'{k}: {parse_object(v, h_level+1)}'
#                         ]
#                     )
#             return '\n'.join(['\n'.join(i) for i in l])
#         if type(obj) is list:
#             l = []
#             for i in obj:
#                 l.append('\t'*(h_level-1)+f'- {parse_object(i, h_level+1)}')
#             return '\n'.join(l)
#         if type(obj) in [int, float, str, type(None)]:
#             return f'{obj}'
#     return parse_object(data, h_level)

# constants = [str, float, int, bool, type(None)]
# containers = [dict, list]

# def parse_object(obj, h_level=1):
#     if type(obj) in containers:
#         ...
#     if type(obj) in constants:
#         return f'{obj}'
#     ...

constants = [str, float, int, bool, type(None)]
containers = [dict, list]

# def parse_object(obj, h_level=0, indent_size=2):
#     indent = ' ' * (h_level * indent_size)
#     if isinstance(obj, dict):
#         lines = []
#         for key, value in obj.items():
#             if isinstance(value, tuple(constants)):
#                 lines.append(f"{indent}{key}: {value}")
#             else:
#                 lines.append(f"{indent}{key}:")
#                 lines.append(parse_object(value, h_level + 1, indent_size))
#         return '\n'.join(lines)
#     elif isinstance(obj, list):
#         lines = []
#         for i, item in enumerate(obj):
#             if isinstance(item, tuple(constants)):
#                 lines.append(f"{indent}- {i+1}. {item}")
#             else:
#                 lines.append(f"{indent}- {i+1}.")
#                 lines.append(parse_object(item, h_level + 1, indent_size))
#         return '\n'.join(lines)
#     elif isinstance(obj, tuple(constants)):
#         return f"{indent}{obj}"
#     else:
#         return f"{indent}<Unsupported type: {type(obj).__name__}>"

def generate_schema(obj, name):
    schema_dict = {
        'name': name,
        'strict': True,
        'schema': parse_schema(obj),
    }
    schema = json.dumps(schema_dict, indent=2)
    return schema

def parse_schema(obj):
    if type(obj) in [dict]:
        required = []
        properties = {}
        for k, v in obj.items():
            properties[k] = parse_schema(v)
            required.append(k)
        return {
            'type':'object',
            'properties': properties,
            "required": required,
            "additionalProperties": False
        }
    if type(obj) in [list]:
        example_item = obj[0]
        item_schema = parse_schema(example_item)
        return {
            'type':'array',
            'items': item_schema,
        }
    if type(obj) in [int, float]:
        return {
            'type':'number',
            'description':'',
        }
    if type(obj) in [str]:
        return {
            'type':'string',
            'description':'',
        }
    


def parse_object(
        obj, 
        indent_size=2, 
        nest_depth=0
    ):
    indent = ' ' * (nest_depth * indent_size)
    if isinstance(obj, dict):
        lines = []
        for key, value in obj.items():
            if isinstance(value, tuple(containers)):
                lines.append(f"{indent}{key}:")
                lines.append(parse_object(value, nest_depth + 1, indent_size))
            if isinstance(value, tuple(constants)):
                lines.append(f"{indent}{key}: {value}")
        return '\n'.join(lines)
    if isinstance(obj, list):
        lines = []
        for i, item in enumerate(obj):
            if isinstance(item, tuple(containers)):
                lines.append(f"{indent}{i+1}: ")
                lines.append(parse_object(item, nest_depth + 1, indent_size))
            if isinstance(item, tuple(constants)):
                lines.append(f"{indent}{i+1}: {item}")
        return '\n'.join(lines)
    if isinstance(obj, tuple(constants)):
        return f"{indent}{obj}"


data = {
    'equipment':{
        'parent': 'john',
        'head':{
            'name':'helmet',
            'color':'blue',
        },
        'torso':{
            'name':'chestplate',
            'color':'green',
            'properties': {
                'strength': 16,
            },
        },
        'rings':[
            {
                'name':'index',
            },
            {
                'color':'blue',
            },
            {
                'properties':{
                    'strength': 10,
                },
            },
            {
                'name':'ring',
            },
            {
                'color':'red',
            },
            'guhguh'
        ]
    },
    'strength':10,
}


# """
# equipment:
#     parent: john
#     head:
#         name: helmet
#     torso:
#         name: chestplate
#     rings:
#     - 
#         name: index 
#         color: red
#     - 
#         name: middle
#     - 
#         name: ring
# """
print(parse_object(data))

#print(generate_schema(data, 'equipment'))
# print(json.dumps(data, indent=2))
# import re
# text = json.dumps(data, indent=2)
# matches = re.findall(r'(\"(.*?)\")', text)
# for match in matches:
#     text = text.replace(match[0], json.loads({'text':match[1]})['text'])
# print(matches)