from keycloak import KeycloakAdmin
import os
class KeycloakRoleHandler:

    def create_role(self, role_name):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )

        return keycloak_admin.create_realm_role({"name": role_name})

    def delete_role(self, role_name):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )

        return keycloak_admin.delete_realm_role(role_name)

    def get_all_roles(self, page, size):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )

        offset = (page - 1) * size
        roles = keycloak_admin.get_realm_roles(query={"first": offset, "max": size})
        return roles

    def get_users_by_role(self, role_name):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )

        return keycloak_admin.get_realm_role_members(role_name)

    def assign_role_to_users(self, user_ids, role_name):
        keycloak_admin = KeycloakAdmin(
            server_url=os.getenv("KEYCLOAK_URL"),
            realm_name=os.getenv("REALM"),
            client_id=os.getenv("CLIENT_ID"),
            client_secret_key=os.getenv("SHARED_SECRET"),
            verify=True
        )
        for uid in user_ids:
            try:
                keycloak_admin.assign_realm_roles(user_id=uid, roles=[role_name])
            except Exception as e:
                raise e

if __name__ == "__main__":
    test = KeycloakRoleHandler()
    # test.create_user("hoang1","hoang1@gmail.com","12345678",[])
    # payload = {
    #     "id": "54e6a776-8cbc-42f1-987f-bc24e03a134b",
    #     "firstName": "John",
    #     "lastName": "Doe",
    #     "email": "hoang1@gmail.com",
    #     "enabled": False
    # }
    test.get_all_roles()

    print("test")