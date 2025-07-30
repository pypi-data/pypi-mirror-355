import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.organization_type import OrganizationType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.membership import Membership
    from ..models.o_parl_location import OParlLocation


T = TypeVar("T", bound="Organization")


@_attrs_define
class Organization:
    """Dieser Objekttyp dient dazu, eine Organisation formal abzubilden. Eine Organisation ist ein Zusammenschluss von
    Personen, die gemeinsam eine Aufgabe erfüllen. Dies kann beispielsweise ein Ausschuss, eine Fraktion oder eine
    Verwaltungseinheit sein. Organisationen können auch hierarchisch strukturiert sein, z.B. eine Fraktion kann
    mehrere Ausschüsse haben.

    WICHTIG: https://www.bonn.sitzung-online.de/public/oparl/organizations?typ=gr&id=354 und
    https://www.bonn.sitzung-online.de/public/oparl/organizations?typ=at&id=354 sind nicht die gleichen Objekte, obwohl
    ihre ID identisch ist. Daher wurde `refid` eingeführt, um die Referenz-ID der Organisation zu speichern, und id
    wird als UUID5 verwendet, um eine eindeutige Identifikation zu gewährleisten.

    see https://oparl.org/spezifikation/online-ansicht/#entity-organization

        Attributes:
            id (UUID):
            id_ref (str):
            name (str):
            organization_type (OrganizationType): Enum for organization types in OParl.

                see https://oparl.org/spezifikation/online-ansicht/#entity-organization
            classification (str):
            short_name (Union[None, Unset, str]):
            web (Union[None, Unset, str]):
            location (Union['OParlLocation', None, Unset]):
            meeting (Union[None, Unset, str]):
            membership (Union[None, Unset, list['Membership']]):
            start_date (Union[None, Unset, datetime.date]):
            end_date (Union[None, Unset, datetime.date]):
    """

    id: UUID
    id_ref: str
    name: str
    organization_type: OrganizationType
    classification: str
    short_name: Union[None, Unset, str] = UNSET
    web: Union[None, Unset, str] = UNSET
    location: Union["OParlLocation", None, Unset] = UNSET
    meeting: Union[None, Unset, str] = UNSET
    membership: Union[None, Unset, list["Membership"]] = UNSET
    start_date: Union[None, Unset, datetime.date] = UNSET
    end_date: Union[None, Unset, datetime.date] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.o_parl_location import OParlLocation

        id = str(self.id)

        id_ref = self.id_ref

        name = self.name

        organization_type = self.organization_type.value

        classification = self.classification

        short_name: Union[None, Unset, str]
        if isinstance(self.short_name, Unset):
            short_name = UNSET
        else:
            short_name = self.short_name

        web: Union[None, Unset, str]
        if isinstance(self.web, Unset):
            web = UNSET
        else:
            web = self.web

        location: Union[None, Unset, dict[str, Any]]
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, OParlLocation):
            location = self.location.to_dict()
        else:
            location = self.location

        meeting: Union[None, Unset, str]
        if isinstance(self.meeting, Unset):
            meeting = UNSET
        else:
            meeting = self.meeting

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "id_ref": id_ref,
                "name": name,
                "organizationType": organization_type,
                "classification": classification,
            }
        )
        if short_name is not UNSET:
            field_dict["shortName"] = short_name
        if web is not UNSET:
            field_dict["web"] = web
        if location is not UNSET:
            field_dict["location"] = location
        if meeting is not UNSET:
            field_dict["meeting"] = meeting
        if membership is not UNSET:
            field_dict["membership"] = membership
        if start_date is not UNSET:
            field_dict["startDate"] = start_date
        if end_date is not UNSET:
            field_dict["endDate"] = end_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.membership import Membership
        from ..models.o_parl_location import OParlLocation

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        id_ref = d.pop("id_ref")

        name = d.pop("name")

        organization_type = OrganizationType(d.pop("organizationType"))

        classification = d.pop("classification")

        def _parse_short_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        short_name = _parse_short_name(d.pop("shortName", UNSET))

        def _parse_web(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        web = _parse_web(d.pop("web", UNSET))

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

        def _parse_meeting(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        meeting = _parse_meeting(d.pop("meeting", UNSET))

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

        organization = cls(
            id=id,
            id_ref=id_ref,
            name=name,
            organization_type=organization_type,
            classification=classification,
            short_name=short_name,
            web=web,
            location=location,
            meeting=meeting,
            membership=membership,
            start_date=start_date,
            end_date=end_date,
        )

        organization.additional_properties = d
        return organization

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
