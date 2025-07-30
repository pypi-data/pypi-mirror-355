import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.membership import Membership
    from ..models.o_parl_location import OParlLocation


T = TypeVar("T", bound="PersonResponse")


@_attrs_define
class PersonResponse:
    """Model for the person response from the OParl API.

    Attributes:
        id (UUID):
        id_ref (str):
        name (str):
        family_name (Union[None, Unset, str]):
        given_name (Union[None, Unset, str]):
        form_of_adress (Union[None, Unset, str]):
        affix (Union[None, Unset, str]):
        gender (Union[None, Unset, str]):
        location (Union['OParlLocation', None, Unset]):
        status (Union[None, Unset, list[str]]):
        membership (Union[None, Unset, list['Membership']]):
        web (Union[None, Unset, str]):
        created (Union[None, Unset, datetime.datetime]):
        modified (Union[None, Unset, datetime.datetime]):
        deleted (Union[Unset, bool]):  Default: False.
        type_ (Union[Unset, str]):  Default: 'https://schema.oparl.org/1.1/Person'.
        membership_ref (Union[None, Unset, list[str]]):
        location_ref (Union[None, Unset, str]):
    """

    id: UUID
    id_ref: str
    name: str
    family_name: Union[None, Unset, str] = UNSET
    given_name: Union[None, Unset, str] = UNSET
    form_of_adress: Union[None, Unset, str] = UNSET
    affix: Union[None, Unset, str] = UNSET
    gender: Union[None, Unset, str] = UNSET
    location: Union["OParlLocation", None, Unset] = UNSET
    status: Union[None, Unset, list[str]] = UNSET
    membership: Union[None, Unset, list["Membership"]] = UNSET
    web: Union[None, Unset, str] = UNSET
    created: Union[None, Unset, datetime.datetime] = UNSET
    modified: Union[None, Unset, datetime.datetime] = UNSET
    deleted: Union[Unset, bool] = False
    type_: Union[Unset, str] = "https://schema.oparl.org/1.1/Person"
    membership_ref: Union[None, Unset, list[str]] = UNSET
    location_ref: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.o_parl_location import OParlLocation

        id = str(self.id)

        id_ref = self.id_ref

        name = self.name

        family_name: Union[None, Unset, str]
        if isinstance(self.family_name, Unset):
            family_name = UNSET
        else:
            family_name = self.family_name

        given_name: Union[None, Unset, str]
        if isinstance(self.given_name, Unset):
            given_name = UNSET
        else:
            given_name = self.given_name

        form_of_adress: Union[None, Unset, str]
        if isinstance(self.form_of_adress, Unset):
            form_of_adress = UNSET
        else:
            form_of_adress = self.form_of_adress

        affix: Union[None, Unset, str]
        if isinstance(self.affix, Unset):
            affix = UNSET
        else:
            affix = self.affix

        gender: Union[None, Unset, str]
        if isinstance(self.gender, Unset):
            gender = UNSET
        else:
            gender = self.gender

        location: Union[None, Unset, dict[str, Any]]
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, OParlLocation):
            location = self.location.to_dict()
        else:
            location = self.location

        status: Union[None, Unset, list[str]]
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, list):
            status = self.status

        else:
            status = self.status

        membership: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.membership, Unset):
            membership = UNSET
        elif isinstance(self.membership, list):
            membership = []
            for membership_type_0_item_data in self.membership:
                membership_type_0_item = membership_type_0_item_data.to_dict()
                membership.append(membership_type_0_item)

        else:
            membership = self.membership

        web: Union[None, Unset, str]
        if isinstance(self.web, Unset):
            web = UNSET
        else:
            web = self.web

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

        membership_ref: Union[None, Unset, list[str]]
        if isinstance(self.membership_ref, Unset):
            membership_ref = UNSET
        elif isinstance(self.membership_ref, list):
            membership_ref = self.membership_ref

        else:
            membership_ref = self.membership_ref

        location_ref: Union[None, Unset, str]
        if isinstance(self.location_ref, Unset):
            location_ref = UNSET
        else:
            location_ref = self.location_ref

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "id_ref": id_ref,
                "name": name,
            }
        )
        if family_name is not UNSET:
            field_dict["familyName"] = family_name
        if given_name is not UNSET:
            field_dict["givenName"] = given_name
        if form_of_adress is not UNSET:
            field_dict["formOfAdress"] = form_of_adress
        if affix is not UNSET:
            field_dict["affix"] = affix
        if gender is not UNSET:
            field_dict["gender"] = gender
        if location is not UNSET:
            field_dict["location"] = location
        if status is not UNSET:
            field_dict["status"] = status
        if membership is not UNSET:
            field_dict["membership"] = membership
        if web is not UNSET:
            field_dict["web"] = web
        if created is not UNSET:
            field_dict["created"] = created
        if modified is not UNSET:
            field_dict["modified"] = modified
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if type_ is not UNSET:
            field_dict["type"] = type_
        if membership_ref is not UNSET:
            field_dict["membership_ref"] = membership_ref
        if location_ref is not UNSET:
            field_dict["location_ref"] = location_ref

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.membership import Membership
        from ..models.o_parl_location import OParlLocation

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        id_ref = d.pop("id_ref")

        name = d.pop("name")

        def _parse_family_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        family_name = _parse_family_name(d.pop("familyName", UNSET))

        def _parse_given_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        given_name = _parse_given_name(d.pop("givenName", UNSET))

        def _parse_form_of_adress(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        form_of_adress = _parse_form_of_adress(d.pop("formOfAdress", UNSET))

        def _parse_affix(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        affix = _parse_affix(d.pop("affix", UNSET))

        def _parse_gender(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        gender = _parse_gender(d.pop("gender", UNSET))

        def _parse_location(data: object) -> Union["OParlLocation", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                location_type_0 = OParlLocation.from_dict(data)

                return location_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlLocation", None, Unset], data)

        location = _parse_location(d.pop("location", UNSET))

        def _parse_status(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                status_type_0 = cast(list[str], data)

                return status_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_membership(data: object) -> Union[None, Unset, list["Membership"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                membership_type_0 = []
                _membership_type_0 = data
                for membership_type_0_item_data in _membership_type_0:
                    membership_type_0_item = Membership.from_dict(membership_type_0_item_data)

                    membership_type_0.append(membership_type_0_item)

                return membership_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Membership"]], data)

        membership = _parse_membership(d.pop("membership", UNSET))

        def _parse_web(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        web = _parse_web(d.pop("web", UNSET))

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

        def _parse_membership_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                membership_ref_type_0 = cast(list[str], data)

                return membership_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        membership_ref = _parse_membership_ref(d.pop("membership_ref", UNSET))

        def _parse_location_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        location_ref = _parse_location_ref(d.pop("location_ref", UNSET))

        person_response = cls(
            id=id,
            id_ref=id_ref,
            name=name,
            family_name=family_name,
            given_name=given_name,
            form_of_adress=form_of_adress,
            affix=affix,
            gender=gender,
            location=location,
            status=status,
            membership=membership,
            web=web,
            created=created,
            modified=modified,
            deleted=deleted,
            type_=type_,
            membership_ref=membership_ref,
            location_ref=location_ref,
        )

        person_response.additional_properties = d
        return person_response

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
