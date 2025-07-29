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

    def get_user_id(self, event, context):
        user_manager = KeycloakUserManagerImpl()
        user_id = event['pathParameters']['id']
        print("userid" + user_id)
        existing_user = user_manager.get_user_id(user_id)
        print(existing_user)
        return existing_user

    def assign_realm_roles(self, event, context):
        user_manager = KeycloakUserManagerImpl()
        body = json.loads(event.get("body", "{}"))
        # 2. Lấy user_id từ request
        user_id = body.get("id")
        role_names = body.get("roles", [])
        return user_manager.assign_roles(user_id, role_names)

handler = UserHandler()

def create(event, context):
    result =  handler.create(event, context)
    return {"statusCode": 200, "body": result }


def delete(event, context):
    result = handler.delete(event, context)
    return {"statusCode": 200, "body": result }

def update(event, context):
    result = handler.update(event, context)
    return {"statusCode": 200, "body": result}

def get_user(event, context):
    result = handler.get_user_id(event, context)
    return {"statusCode": 200, "body": json.dumps(result, indent=2) }

def assign_roles(event, context):
    result = handler.assign_realm_roles(event, context)
    return {"statusCode": 200, "body": json.dumps(result, indent=2) }
