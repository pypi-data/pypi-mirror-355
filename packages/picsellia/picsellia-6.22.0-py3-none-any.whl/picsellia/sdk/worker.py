from typing import Union
from uuid import UUID

from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.types.enums import WorkerType
from picsellia.types.schemas import WorkerSchema


class Worker(Dao):
    def __init__(self, connexion: Connexion, data: dict, type: Union[WorkerType, str]):
        Dao.__init__(self, connexion, data)
        self.type = WorkerType.validate(type)

    @property
    def username(self) -> str:
        """Username of the Worker"""
        return self._username

    @property
    def user_id(self) -> UUID:
        """id of the User"""
        return self._user_id

    def __str__(self):
        return (
            f"{Colors.UNDERLINE}Worker '{self.username}' of a {self.type} {Colors.ENDC}"
        )

    @exception_handler
    @beartype
    def sync(self) -> dict:
        if self.type == WorkerType.DATASET:
            r = self.connexion.get(f"/api/worker/{self.id}").json()
        elif self.type == WorkerType.DEPLOYMENT:
            r = self.connexion.get(f"/api/deploymentpermissionner/{self.id}").json()
        else:
            raise ValueError("This type of Worker cannot be used at the moment")
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def refresh(self, data: dict) -> WorkerSchema:
        schema = WorkerSchema(**data)
        self._username = schema.collaborator.username
        self._user_id = schema.collaborator.user_id
        return schema

    @exception_handler
    @beartype
    def get_infos(self) -> dict:
        """Retrieve worker info

        Examples:
            ```python
            worker = my_dataset.list_workers()[0]
            print(worker.get_infos())
            ```

        Returns:
            A dict with data of the worker
        """
        return {"username": self.username}
