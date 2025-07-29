import abc
from pydantic import StrictStr
from typing import TYPE_CHECKING, Optional, List

from istari_digital_client.models.access_relationship import AccessRelationship
from istari_digital_client.models.access_subject_type import AccessSubjectType
from istari_digital_client.models.access_relation import AccessRelation
from istari_digital_client.models.access_resource_type import AccessResourceType
from istari_digital_client.models.update_access_relationship import UpdateAccessRelationship

if TYPE_CHECKING:
    from istari_digital_client.api.client_api import ClientApi


class Shareable(abc.ABC):
    @property
    @abc.abstractmethod
    def client(self) -> Optional["ClientApi"]: ...

    @property
    def _resource_id(self) -> StrictStr:
        resource_id = getattr(self, "id", None)

        if resource_id is None:
            raise ValueError("id is not set")

        return resource_id

    @property
    def _resource_type(self) -> AccessResourceType:
        class_name = self.__class__.__name__

        try:
            return AccessResourceType(class_name.lower())
        except ValueError as e:
            raise ValueError(
                f"Invalid resource type for {class_name}. "
                f"Ensure the class name is a valid AccessResourceType."
            ) from e

    def create_access(
        self,
        subject_type: AccessSubjectType,
        subject_id: str,
        relation: AccessRelation,
    ) -> AccessRelationship:
        if not self.client:
            raise ValueError("client is not set")

        access_relationship = AccessRelationship(
            subject_type=subject_type,
            subject_id=subject_id,
            relation=relation,
            resource_type=self._resource_type,
            resource_id=self._resource_id,
        )

        return self.client.create_access(
            access_relationship=access_relationship,
        )

    def create_access_by_email(
        self,
        subject_type: AccessSubjectType,
        subject_email: StrictStr,
        relation: AccessRelation,
    ) -> AccessRelationship:
        if not self.client:
            raise ValueError("client is not set")

        return self.client.create_access_by_email_for_other_tenants(
            subject_type=subject_type,
            email=subject_email,
            resource_type=self._resource_type,
            resource_id=self._resource_id,
            access_relationship=relation,
        )

    def update_access(
        self,
        subject_type: AccessSubjectType,
        subject_id: StrictStr,
        relation: AccessRelation,
    ) -> AccessRelationship:
        if not self.client:
            raise ValueError("client is not set")

        update_access_relationship = UpdateAccessRelationship(
            relation=relation,
        )

        return self.client.update_access(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=self._resource_type,
            resource_id=self._resource_id,
            update_access_relationship=update_access_relationship,
        )

    def remove_access(
        self,
        subject_type: AccessSubjectType,
        subject_id: StrictStr,
    ) -> None:
        if not self.client:
            raise ValueError("client is not set")

        self.client.remove_access(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=self._resource_type,
            resource_id=self._resource_id,
        )

    def list_access(self) -> List[AccessRelationship]:
        if not self.client:
            raise ValueError("client is not set")

        return self.client.list_access(
            resource_type=self._resource_type,
            resource_id=self._resource_id,
        )
