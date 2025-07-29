from abc import ABC, abstractmethod
# Abstract base class
class User(ABC):

    @abstractmethod
    def create_user(self, username, email, password, roles=[]):
        pass  # This method must be overridden by subclasses

    @abstractmethod
    def update_user(self, payload):
        pass  # This method must be overridden by subclasses

    @abstractmethod
    def get_user_id(self, username):
        pass  # This method must be overridden by subclasses

    @abstractmethod
    def assign_roles(self, user_id, roles):
        pass

    @abstractmethod
    def delete_user(self, user_id):
        pass