from abc import ABC, abstractmethod

# Abstract base class

class Role(ABC):

    @abstractmethod
    def create_role(self, role_name):
        pass  # This method must be overridden by subclasses

    @abstractmethod
    def delete_role(self, role_name):
        pass

    @abstractmethod
    def get_all_roles(self):
        pass
    @abstractmethod
    def get_users_by_role(self, role_name):
        pass
