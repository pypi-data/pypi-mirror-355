import logging
from typing import Optional

import orjson
from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.types.enums import ProcessingType
from picsellia.types.schemas import ProcessingSchema
from picsellia.utils import filter_payload

logger = logging.getLogger("picsellia")


class Processing(Dao):
    def __init__(self, connexion: Connexion, data: dict):
        Dao.__init__(self, connexion, data)

    @property
    def name(self) -> str:
        """Name of this (Processing)"""
        return self._name

    @property
    def type(self) -> ProcessingType:
        """Type of this (Processing)"""
        return self._type

    @property
    def docker(self) -> str:
        """Docker image of this (Processing)"""
        return f"{self._docker_image}:{self._docker_tag}"

    def __str__(self):
        return f"{Colors.GREEN}Processing '{self.name}' {Colors.ENDC} (id: {self.id})"

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"/api/processing/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def refresh(self, data: dict) -> ProcessingSchema:
        schema = ProcessingSchema(**data)
        self._name = schema.name
        self._type = schema.type
        self._docker_image = schema.docker_image
        self._docker_tag = schema.docker_tag
        return schema

    @exception_handler
    @beartype
    def update(
        self,
        docker_image: Optional[str] = None,
        docker_tag: Optional[str] = None,
        description: Optional[str] = None,
        default_parameters: Optional[dict] = None,
        default_cpu: Optional[int] = None,
        default_gpu: Optional[int] = None,
    ) -> None:
        """Update docker_image, description or default_parameters of (Processing).

        Examples:
            ```python
            processing.update(docker_image='new-image', docker_tag='1.2.0')
            ```

        Arguments:
            docker_image (str, optional): New docker image of this (Processing). Defaults to None.
            docker_tag (str, optional): New docker tag of this (Processing). Defaults to None.
            description (str, optional): New description of the (Processing). Defaults to None.
            default_parameters (dict, optional): New default parameters of the (Processing). Defaults to None.
            default_cpu (str or InferenceType, optional): New default cpu of the (Processing). Defaults to None.
            default_gpu (str or InferenceType, optional): New default gpu of the (Processing). Defaults to None.
        """
        payload = {
            "docker_image": docker_image,
            "docker_tag": docker_tag,
            "description": description,
            "default_parameters": default_parameters,
            "default_cpu": default_cpu,
            "default_gpu": default_gpu,
        }
        filtered_payload = filter_payload(payload)
        r = self.connexion.patch(
            f"/sdk/processing/{self.id}", data=orjson.dumps(filtered_payload)
        ).json()
        self.refresh(r)
        logger.info(f"{self} updated")

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete this processing from the platform.

        :warning: **DANGER ZONE**: Be very careful here!

        Examples:
            ```python
            processing.delete()
            ```
        """
        self.connexion.delete(f"/sdk/processing/{self.id}")
        logger.info(f"{self} deleted.")
