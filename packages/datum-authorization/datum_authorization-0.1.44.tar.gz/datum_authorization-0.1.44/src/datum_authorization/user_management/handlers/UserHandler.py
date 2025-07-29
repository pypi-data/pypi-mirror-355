import json

from datum_authorization.user_management.keycloak.keycloak_user import KeycloakUserManagerImpl

class UserHandler:
    def create(self, event, context):
        body = json.loads(event['body'])
        user_manager = KeycloakUserManagerImpl()
        username = body.get("username")
        email = body.get("email")
        password = body.get("password")
        roles = body.get("roles", [])  # Default to empty list if not provided
        return user_manager.create_user(username, email, password, roles)

    def delete(self, event, context):
        return {"statusCode": 200, "body": "User deleted"}

    def update(self, event, context):
        body = json.loads(event['body'])
        user_manager = KeycloakUserManagerImpl()
        return user_manager.update_user(body)

    def get_user_id(event, context):
        user_manager = KeycloakUserManagerImpl()
        body = json.loads(event.get("body", "{}"))
        # 2. Lấy user_id từ request
        user_id = body.get("id")
        return user_manager.get_user_id(user_id)

    def assign_realm_roles(event, context):
        user_manager = KeycloakUserManagerImpl()
        body = json.loads(event.get("body", "{}"))
        # 2. Lấy user_id từ request
        user_id = body.get("id")
        role_names = body.get("roles", [])
        return user_manager.assign_roles(user_id, role_names)

handler = UserHandler()

def create(event, context):
    return handler.create(event, context)

def delete(event, context):
    return handler.delete(event, context)

def update(event, context):
    return handler.update(event, context)

def get_user(event, context):
    return handler.get_user_id(event, context)

def assign_roles(event, context):
    return handler.assign_realm_roles(event, context)
