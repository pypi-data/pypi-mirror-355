import logging

import orjson
from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.types.schemas import LabelSchema

logger = logging.getLogger("picsellia")


class Label(Dao):
    def __init__(self, connexion: Connexion, data: dict) -> None:
        Dao.__init__(self, connexion, data)

    @property
    def name(self) -> str:
        """Name of this (Label)"""
        return self._name

    def __str__(self):
        return f"{Colors.GREEN}Label '{self.name}'{Colors.ENDC} (id: {self.id})"

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"/api/label/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def refresh(self, data: dict) -> LabelSchema:
        schema = LabelSchema(**data)
        self._name = schema.name
        return schema

    @exception_handler
    @beartype
    def update(self, name: str) -> None:
        """Update this label with a new name.

        Examples:
            ```python
            a_label.update(name="new name")
            ```

        Arguments:
            name: New name of this label
        """
        payload = {"name": name}
        r = self.connexion.patch(
            f"/api/label/{self.id}", data=orjson.dumps(payload)
        ).json()
        self.refresh(r)
        logger.info(f"{self} updated")

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete this label from the platform.
        All annotations shape with this label will be deleted!
        This is a very dangerous move.

        :warning: **DANGER ZONE**: Be very careful here!

        Examples:
            ```python
            this_label.delete()
            ```
        """
        self.connexion.delete(f"/api/label/{self.id}")
        logger.info(f"{self} deleted.")
