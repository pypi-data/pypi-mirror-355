from typing import Self, Type
from uuid import UUID

from rest_framework.serializers import ModelSerializer


def is_uuid(val:str, ver:int=4) -> bool:
    try:
        uuid_obj = UUID(val, version=ver)
        return str(uuid_obj) == val
    except ValueError:
        return False


class SchemaField:
    
    def __init__(self, name:str, schema:dict):
    
        self.error = None
        self.name = name
        self.typ = str(schema['typ']) if 'typ' in schema else None
        self.req = bool(schema['req']) if 'req' in schema else True
        self.min = int(schema['min']) if 'min' in schema else 0
        self.max = int(schema['max']) if 'max' in schema else 0
        self.len = int(schema['len']) if 'len' in schema else 0
        self.iss = str(schema['iss']) if 'iss' in schema else f"Field '{name}' is either missing or invalid."
        
        if not (self.typ and self.typ in ['int', 'bool', 'str', 'uuid', 'float', 'list', 'dict']) :
            self.error = f"Schema field '{name}' has missing/invalid 'type' attribute."


class Validation:
    
    def __init__(self, serializer: Type[ModelSerializer]):
        
        # ViewSet
        self.serializer = serializer
        
        # Command
        self.queryset = None
        self.serializer = None
        
        # Here
        self.errors = []
        self.is_valid = True
        self.data = None

    def validate(self, field:SchemaField, key:str, value:any) -> None:
        hints = []
        
        if field.req == True and bool(value is None or value == ''):
            hints.append(f"Field '{key}' is required.")
            
        if field.min > 0 and len(value) < field.min:
            hints.append(f"Field '{key}' must have a minimum lenght of {str(field.min)}.")
            
        if 0 < field.max < len(value):
            hints.append(f"Field '{key}' must have a maximum lenght of {str(field.max)}.")
            
        if field.len > 0 and not (len(value) == field.len):
            hints.append(f"Field '{key}' must be of lenght {str(field.len)}.")
            
        if field.typ == 'uuid':
            if not is_uuid(val=value):
                hints.append(f"Field '{key}' is not a valid UUID.")
        elif type(value).__name__ != field.typ:
            hints.append(f"Field '{key}' must be of type {field.typ}, {type(value).__name__} provided.")
            
        if len(hints) > 0:
            self.errors.append({
                'type': "VALIDATION ERROR",
                'field': key,
                'error': field.iss,
                'hints': hints
            })

        
    def check(self, schema: dict, data: dict) -> None:
        for key in list(schema.keys()):
            field = SchemaField(name=key, schema=schema[key])
            if field.error:
                self.errors.append({
                    'type': "SCHEMA ERROR",
                    'field': key,
                    'error': field.error
                })
            
            value = data[key] if key in  data else None
            
            if field.typ == 'dict':
                self.check(schema=schema[key], data=value)
            
            self.validate(field=field, key=key, value=value)
            
        if len(self.errors) > 0:
            self.is_valid = False


    def get(self) -> Self:
        serialize = self.serializer(self.queryset, many=False)
        self.data = serialize.data
        return self