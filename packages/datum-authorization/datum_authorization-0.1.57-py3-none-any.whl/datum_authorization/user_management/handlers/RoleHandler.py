import json
from datum_authorization.user_management.keycloak.keycloak_role import KeycloakRoleHandler

class RoleHandler:
    def create(self, event, context):
        body = json.loads(event['body'])
        role_name = body.get("name")

        role_manager = KeycloakRoleHandler()
        return role_manager.create_role(role_name)

    def delete(self, event, context):
        role_name = event['pathParameters']['name']
        role_manager = KeycloakRoleHandler()
        role_manager.delete_role(role_name)

    def get_all(self, event, context):
        page = int(event.get("queryStringParameters", {}).get("page", 1))
        size = int(event.get("queryStringParameters", {}).get("size", 50))
        role_manager = KeycloakRoleHandler()
        roles = role_manager.get_all_roles(page, size)
        return {
            "roles": roles
        }

    def assign_role_to_user(self, event, context):
        body = json.loads(event['body'])
        user_id = body.get("userId")
        role_name = body.get("role")

        role_manager = KeycloakRoleHandler()
        return role_manager.assign_roles_to_user(user_id, [role_name])

    def get_users_by_role(self, event, context):
        user_id = event['pathParameters']['userId']
        role_manager = KeycloakRoleHandler()
        return role_manager.get_users_by_role(user_id)

    def assign_role_to_users(self, event, context):
        body = json.loads(event['body'])
        role_manager = KeycloakRoleHandler()
        role_name = body.get("role")
        user_ids = body.get("user_ids")
        return role_manager.assign_role_to_users(user_ids, [role_name])

handler = RoleHandler()

def create_role(event, context):
    role_name = handler.create(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "role_name": role_name
        })
    }


def delete_role(event, context):
    handler.delete(event, context)
    return {
        "statusCode": 204,
        "body": ""
    }


def get_users_by_role(event, context):
    result = handler.get_users_by_role(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps(result, indent=2)
    }


def assign_role_to_users(event, context):
    user_id = handler.assign_role_to_users(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_id
        }, indent=2)
    }

def get_all(event, context):
    result = handler.get_all(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps(result, indent=2)
    }
