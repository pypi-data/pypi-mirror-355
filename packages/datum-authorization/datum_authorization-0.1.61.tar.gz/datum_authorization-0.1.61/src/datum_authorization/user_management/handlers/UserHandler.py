import json
from datum_authorization.user_management.keycloak.keycloak_user import KeycloakUserHandler


class UserHandler:
    def create(self, event, context):
        body = json.loads(event['body'])
        user_manager = KeycloakUserHandler()
        username = body.get("username")
        email = body.get("email")
        password = body.get("password")
        roles = body.get("roles", [])  # Default to empty list if not provided
        return user_manager.create_user(username, email, password, roles)

    def delete(self, event, context):
        return {"statusCode": 200, "body": "User deleted"}

    def update(self, event, context):
        body = json.loads(event['body'])
        user_manager = KeycloakUserHandler()
        return user_manager.update_user(body)

    def get_user_id(self, event, context):
        user_manager = KeycloakUserHandler()
        user_id = event['pathParameters']['id']
        print("userid: " + user_id)
        existing_user = user_manager.get_user_id(user_id)
        print(existing_user)
        return existing_user

    def assign_realm_roles(self, event, context):
        user_manager = KeycloakUserHandler()
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("id")
        role_names = body.get("roles", [])
        return user_manager.assign_roles(user_id, role_names)


    def get_all(self, event, context):
        page = int(event.get("queryStringParameters", {}).get("page", 1))
        size = int(event.get("queryStringParameters", {}).get("size", 50))
        user_manager = KeycloakUserHandler()

        result = user_manager.get_all(page, size)
        return {
           "page": page,
           "size": size,
           "users": result
        }


handler = UserHandler()


def create_user(event, context):
    user_id = handler.create(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_id
        })
    }


def delete_user(event, context):
    result = handler.delete(event, context)
    return {
        "statusCode": 200,
        "body": result
    }


def update_user(event, context):
    user_id = handler.update(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_id
        })
    }


def get_user(event, context):
    result = handler.get_user_id(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps(result, indent=2)
    }


def assign_roles_to_user(event, context):
    user_id = handler.assign_realm_roles(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_id
        }, indent=2)
    }


def get_all_user(event, context):
    result = handler.get_all(event, context)
    return {
        "statusCode": 200,
        "body": json.dumps(result, indent=2)
    }
