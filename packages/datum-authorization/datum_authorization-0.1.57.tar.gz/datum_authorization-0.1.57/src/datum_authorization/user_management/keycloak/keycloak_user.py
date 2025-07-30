
from keycloak import KeycloakAdmin
import os
import json

class KeycloakUserHandler:
    def create_user(self, username, email, password, roles=[]):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )

        print(json.dumps({
            "email": email,
            "username": username,
            "enabled": True,
            "firstName": "John",
            "lastName": "Doe",
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False  # 👈 this is often required
            }]
        }, indent=2))

        user_id = keycloak_admin.create_user({
            "email": email,
            "username": username,
            "enabled": True,
            "firstName": "John",
            "lastName": "Doe",
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False  # 👈 this is often required
            }]
        })

        print("user_id")
        print(user_id)

        if roles:
            self.assign_roles(user_id, roles)
        return user_id
    def update_user(self, payload):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        user_id = payload.get("id")
        if not user_id:
            raise ValueError("User ID ('id') is required in the payload.")
        updated_user = {
            "firstName": payload.get("firstName"),
            "lastName": payload.get("lastName"),
            "enabled": payload.get("enabled", True)  # default to True if not specified
        }
        updated_user = {k: v for k, v in updated_user.items() if v is not None}

        keycloak_admin.update_user(user_id=user_id, payload=updated_user)

        roles = payload.get("roles", [])
        if roles:
            # Get all available roles from realm
            all_roles = keycloak_admin.get_realm_roles()

            # Match and extract role representations from names
            matched_roles = [role for role in all_roles if role["name"] in roles]
            if matched_roles:
                keycloak_admin.assign_realm_roles(user_id=user_id, roles=matched_roles)
        return user_id

    def get_user_id(self, username):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        users = keycloak_admin.get_users({"username": username})
        return users[0] if users else None
    def assign_roles(self, user_id, roles):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        realm_roles = [keycloak_admin.get_realm_role(role) for role in roles]
        keycloak_admin.assign_realm_roles(user_id=user_id, roles=realm_roles)
        return user_id

    def delete_user(self, user_id):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        keycloak_admin.delete_user(user_id)

    def assign_roles(self, user_id, roles):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        realm_roles = [keycloak_admin.get_realm_role(role) for role in roles]
        keycloak_admin.assign_realm_roles(user_id=user_id, roles=realm_roles)
        return user_id

    def get_all(self, page, size):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )

        offset = (page - 1) * size
        users = keycloak_admin.get_users(query={"first": offset, "max": size})

        results = []
        for user in users:
            roles = keycloak_admin.get_realm_roles_of_user(user["id"])
            results.append({
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "roles": [r["name"] for r in roles]
            })

        return results

if __name__ == "__main__":
    test = KeycloakUserHandler()
    # test.create_user("hoang1","hoang1@gmail.com","12345678",[])
    # payload = {
    #     "id": "54e6a776-8cbc-42f1-987f-bc24e03a134b",
    #     "firstName": "John",
    #     "lastName": "Doe",
    #     "email": "hoang1@gmail.com",
    #     "enabled": False
    # }
    test.get_all(page=1, size=20)

    print("test")