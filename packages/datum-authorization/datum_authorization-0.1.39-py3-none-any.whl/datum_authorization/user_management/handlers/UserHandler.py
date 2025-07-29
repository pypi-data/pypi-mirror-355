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
        user_manager.create_user(username, email, password, roles)

    def delete(self, event, context):
        return {"statusCode": 200, "body": "User deleted"}

handler = UserHandler()

def create(event, context):
    return handler.create(event, context)

def delete(event, context):
    return handler.delete(event, context)