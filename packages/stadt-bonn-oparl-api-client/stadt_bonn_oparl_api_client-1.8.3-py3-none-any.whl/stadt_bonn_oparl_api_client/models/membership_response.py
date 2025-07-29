import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.organization import Organization
    from ..models.person import Person


T = TypeVar("T", bound="MembershipResponse")


@_attrs_define
class MembershipResponse:
    """Model for the membership response from the OParl API.

    Attributes:
        id (UUID):
        id_ref (str):
        person (Union['Person', None, Unset]):
        organization (Union['Organization', None, Unset]):
        role (Union[None, Unset, str]):
        voting_right (Union[None, Unset, bool]):  Default: False.
        start_date (Union[None, Unset, datetime.date]):
        end_date (Union[None, Unset, datetime.date]):
        created (Union[None, Unset, datetime.datetime]):
        modified (Union[None, Unset, datetime.datetime]):
        deleted (Union[Unset, bool]):  Default: False.
        type_ (Union[Unset, str]):  Default: 'https://schema.oparl.org/1.1/Membership'.
        person_ref (Union[None, Unset, str]):
        organization_ref (Union[None, Unset, str]):
    """

    id: UUID
    id_ref: str
    person: Union["Person", None, Unset] = UNSET
    organization: Union["Organization", None, Unset] = UNSET
    role: Union[None, Unset, str] = UNSET
    voting_right: Union[None, Unset, bool] = False
    start_date: Union[None, Unset, datetime.date] = UNSET
    end_date: Union[None, Unset, datetime.date] = UNSET
    created: Union[None, Unset, datetime.datetime] = UNSET
    modified: Union[None, Unset, datetime.datetime] = UNSET
    deleted: Union[Unset, bool] = False
    type_: Union[Unset, str] = "https://schema.oparl.org/1.1/Membership"
    person_ref: Union[None, Unset, str] = UNSET
    organization_ref: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.organization import Organization
        from ..models.person import Person

        id = str(self.id)

        id_ref = self.id_ref

        person: Union[None, Unset, dict[str, Any]]
        if isinstance(self.person, Unset):
            person = UNSET
        elif isinstance(self.person, Person):
            person = self.person.to_dict()
        else:
            person = self.person

        organization: Union[None, Unset, dict[str, Any]]
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, Organization):
            organization = self.organization.to_dict()
        else:
            organization = self.organization

        role: Union[None, Unset, str]
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        voting_right: Union[None, Unset, bool]
        if isinstance(self.voting_right, Unset):
            voting_right = UNSET
        else:
            voting_right = self.voting_right

        start_date: Union[None, Unset, str]
        if isinstance(self.start_date, Unset):
            start_date = UNSET
        elif isinstance(self.start_date, datetime.date):
            start_date = self.start_date.isoformat()
        else:
            start_date = self.start_date

        end_date: Union[None, Unset, str]
        if isinstance(self.end_date, Unset):
            end_date = UNSET
        elif isinstance(self.end_date, datetime.date):
            end_date = self.end_date.isoformat()
        else:
            end_date = self.end_date

        created: Union[None, Unset, str]
        if isinstance(self.created, Unset):
            created = UNSET
        elif isinstance(self.created, datetime.datetime):
            created = self.created.isoformat()
        else:
            created = self.created

        modified: Union[None, Unset, str]
        if isinstance(self.modified, Unset):
            modified = UNSET
        elif isinstance(self.modified, datetime.datetime):
            modified = self.modified.isoformat()
        else:
            modified = self.modified

        deleted = self.deleted

        type_ = self.type_

        person_ref: Union[None, Unset, str]
        if isinstance(self.person_ref, Unset):
            person_ref = UNSET
        else:
            person_ref = self.person_ref

        organization_ref: Union[None, Unset, str]
        if isinstance(self.organization_ref, Unset):
            organization_ref = UNSET
        else:
            organization_ref = self.organization_ref

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "id_ref": id_ref,
            }
        )
        if person is not UNSET:
            field_dict["person"] = person
        if organization is not UNSET:
            field_dict["organization"] = organization
        if role is not UNSET:
            field_dict["role"] = role
        if voting_right is not UNSET:
            field_dict["votingRight"] = voting_right
        if start_date is not UNSET:
            field_dict["startDate"] = start_date
        if end_date is not UNSET:
            field_dict["endDate"] = end_date
        if created is not UNSET:
            field_dict["created"] = created
        if modified is not UNSET:
            field_dict["modified"] = modified
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if type_ is not UNSET:
            field_dict["type"] = type_
        if person_ref is not UNSET:
            field_dict["person_ref"] = person_ref
        if organization_ref is not UNSET:
            field_dict["organization_ref"] = organization_ref

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.organization import Organization
        from ..models.person import Person

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        id_ref = d.pop("id_ref")

        def _parse_person(data: object) -> Union["Person", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                person_type_0 = Person.from_dict(data)

                return person_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Person", None, Unset], data)

        person = _parse_person(d.pop("person", UNSET))

        def _parse_organization(data: object) -> Union["Organization", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                organization_type_0 = Organization.from_dict(data)

                return organization_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Organization", None, Unset], data)

        organization = _parse_organization(d.pop("organization", UNSET))

        def _parse_role(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        role = _parse_role(d.pop("role", UNSET))

        def _parse_voting_right(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        voting_right = _parse_voting_right(d.pop("votingRight", UNSET))

        def _parse_start_date(data: object) -> Union[None, Unset, datetime.date]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_date_type_0 = isoparse(data).date()

                return start_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.date], data)

        start_date = _parse_start_date(d.pop("startDate", UNSET))

        def _parse_end_date(data: object) -> Union[None, Unset, datetime.date]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_date_type_0 = isoparse(data).date()

                return end_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.date], data)

        end_date = _parse_end_date(d.pop("endDate", UNSET))

        def _parse_created(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_type_0 = isoparse(data)

                return created_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        created = _parse_created(d.pop("created", UNSET))

        def _parse_modified(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modified_type_0 = isoparse(data)

                return modified_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        modified = _parse_modified(d.pop("modified", UNSET))

        deleted = d.pop("deleted", UNSET)

        type_ = d.pop("type", UNSET)

        def _parse_person_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        person_ref = _parse_person_ref(d.pop("person_ref", UNSET))

        def _parse_organization_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        organization_ref = _parse_organization_ref(d.pop("organization_ref", UNSET))

        membership_response = cls(
            id=id,
            id_ref=id_ref,
            person=person,
            organization=organization,
            role=role,
            voting_right=voting_right,
            start_date=start_date,
            end_date=end_date,
            created=created,
            modified=modified,
            deleted=deleted,
            type_=type_,
            person_ref=person_ref,
            organization_ref=organization_ref,
        )

        membership_response.additional_properties = d
        return membership_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
