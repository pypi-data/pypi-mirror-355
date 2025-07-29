from datum_authorization.user_management.user import User

from keycloak import KeycloakAdmin
import os



class KeycloakUserManagerImpl(User):

    def create_user(self, username, email, password, roles=[]):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
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
            "email": payload.get("email"),
            "enabled": payload.get("enabled", True)  # default to True if not specified
        }
        updated_user = {k: v for k, v in updated_user.items() if v is not None}

        keycloak_admin.update_user(user_id=user_id, payload=updated_user)

    def get_user_id(self, username):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        users = keycloak_admin.get_users({"username": username})
        return users[0]["id"] if users else None
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

if __name__ == "__main__":
    test = KeycloakUserManagerImpl()
    # test.create_user("hoang1","hoang1@gmail.com","12345678",[])
    # payload = {
    #     "id": "54e6a776-8cbc-42f1-987f-bc24e03a134b",
    #     "firstName": "John",
    #     "lastName": "Doe",
    #     "email": "hoang1@gmail.com",
    #     "enabled": False
    # }
    test.assign_roles("54e6a776-8cbc-42f1-987f-bc24e03a134b",["admin"])

    print("test")