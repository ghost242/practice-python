"""
Research about json schema with pydantic.
This modulle for testing about generation models from json schema document.
"""

from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser


# schema = """{
#     "$schema": "https://json-schema.org/draft/2020-12/schema",
#     "$id": "urn:resource:policy:document",
#     "title": "ResourcePolicy",
#     "type": "object",
#     "properties": {
#         "resource": {
#             "type": "object",
#             "properties": {
#                 "resourceId": {
#                     "type": "string",
#                     "description": "Representation resource name followed by URN(urn:resource:{teamId}:{projectId}:{documentId})",
#                     "pattern": "^urn:resource(:[a-zA-Z0-9]+){3}$"
#                 },
#                 "isPublic": {"type": "boolean"},
#                 "isDeleted": {"type": "boolean"},
#                 "creatorId": {"type": "string"}
#             }
#         },
#         "policies": {
#             "type": "array",
#             "items": {
#                 "$ref": "#/$defs/resource_policy"
#             }
#         },
#         "creator": {
#             "type": "string",
#             "description": "User ID which identifier of document creator"
#         },
#         "updatedAt": {
#             "type": "string",
#             "description": "Latest recent modfied timestamp(ISO 8601)"
#         },
#         "createdAt": {
#             "type": "string",
#             "description": "Created timestamp(ISO 8601)"
#         }
#     },
#     "required": ["resource", "policies", "creator", "updatedAt", "createdAt"],
#     "$defs": {
#         "resource_policy": {
#             "type": "object",
#             "properties": {
#                 "permissions": {
#                     "type": "array",
#                     "items": {
#                         "enum": [
#                             "can_view",
#                             "can_edit",
#                             "can_delete",
#                             "can_share"
#                         ]
#                     }
#                 },
#                 "effect": {"enum": ["allow", "deny"]},
#                 "priority": {
#                     "type": "integer",
#                     "minimum": 0,
#                     "exclusiveMaximum": 100
#                 },
#                 "targets": {
#                     "type": "array",
#                     "items": {"type": "string"},
#                     "minContains": 1,
#                     "uniqueItems": true
#                 }
#             },
#             "required": ["permissions", "effect", "priority", "targets"]
#         }
#     }
# }"""

schema = """{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:user:policy:document",
    "title": "UserPolicy",
    "type": "object",
    "properties":  {
        "policies": {
            "type": "array",
            "items": {
                "$ref": "#/$defs/user_policy"
            }
        },
        "updatedAt": {
            "type": "string",
            "description": "Latest recent modfied timestamp(ISO 8601)"
        },
        "createdAt": {
            "type": "string",
            "description": "Created timestamp(ISO 8601)"
        }
    },
    "required": ["policies", "updatedAt", "createdAt"],
    "$defs": {
        "user_policy": {
            "type": "object",
            "properties": {
                "resourceId": {
                    "type": "string",
                    "description": "Representation resource name followed by URN(urn:resource:{teamId}[:{projectId}[:{documentId}]])",
                    "pattern": "^urn:resource(:[a-zA-Z0-9]+{1,3})$"
                },
                "permissions": {
                    "type": "array",
                    "items": {
                        "enum": ["can_view", "can_edit", "can_delete", "can_share"]
                    },
                    "uniqueItems": true
                },
                "effect": {
                    "enum": ["allow", "deny"]
                }
            },
            "required": ["resourceId", "permissions", "effect"]
        }
    }
}"""

data_model_types = get_data_model_types(
    DataModelType.PydanticV2BaseModel,
    target_python_version=PythonVersion.PY_313,
)
parser = JsonSchemaParser(
    schema,
    data_model_type=data_model_types.data_model,
    data_model_root_type=data_model_types.root_model,
    data_model_field_type=data_model_types.field_model,
    data_type_manager_type=data_model_types.data_type_manager,
    dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
)

res = parser.parse()

print(type(res), res)
