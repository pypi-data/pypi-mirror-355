import json
from datum_authorization.user_management.keycloak.keycloak_role import KeycloakRoleHandler
import os

keycloak_role_handler = KeycloakRoleHandler()
handlers = {
    "KEYCLOAK": keycloak_role_handler
}
auth_provider = os.getenv("AUTH_PROVIDER", "KEYCLOAK")

handler = handlers.get(auth_provider)

class RoleHandlerManager:
    def create(self, event, context):
        body = json.loads(event['body'])
        role_name = body.get("name")

        return handler.create_role(role_name)

    def delete(self, event, context):
        role_name = event['pathParameters']['name']
        handler.delete_role(role_name)

    def get_all(self, event, context):
        page = int(event.get("queryStringParameters", {}).get("page", 1))
        size = int(event.get("queryStringParameters", {}).get("size", 50))
        roles = handler.get_all_roles(page, size)
        return {
            "roles": roles,
            "page": page,
            "size": size,
        }

    def assign_role_to_user(self, event, context):
        body = json.loads(event['body'])
        user_id = body.get("userId")
        role_name = body.get("role")

        return handler.assign_roles_to_user(user_id, [role_name])

    def get_users_by_role(self, event, context):
        user_id = event['pathParameters']['userId']
        return handler.get_users_by_role(user_id)

    def assign_role_to_users(self, event, context):
        body = json.loads(event['body'])
        role_manager = KeycloakRoleHandler()
        role_name = body.get("role")
        user_ids = body.get("user_ids")
        return role_manager.assign_role_to_users(user_ids, [role_name])

role_handler_manager = RoleHandlerManager()
def create_role(event, context):
    role_name = role_handler_manager.create(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "role_name": role_name
        })
    }


def delete_role(event, context):
    role_handler_manager.delete(event, context)
    return {
        "statusCode": 204,
        "body": ""
    }


def get_users_by_role(event, context):
    result = role_handler_manager.get_users_by_role(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps(result, indent=2)
    }


def assign_role_to_users(event, context):
    user_id = role_handler_manager.assign_role_to_users(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_id
        }, indent=2)
    }

def get_all_role(event, context):
    result = role_handler_manager.get_all(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps(result, indent=2)
    }
