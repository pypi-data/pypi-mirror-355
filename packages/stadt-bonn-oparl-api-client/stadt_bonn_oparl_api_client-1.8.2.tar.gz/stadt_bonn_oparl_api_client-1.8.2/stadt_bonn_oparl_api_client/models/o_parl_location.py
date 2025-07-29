from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.o_parl_location_geojson_type_0 import OParlLocationGeojsonType0


T = TypeVar("T", bound="OParlLocation")


@_attrs_define
class OParlLocation:
    """Dieser Objekttyp dient dazu, einen Ortsbezug formal abzubilden. Ortsangaben können sowohl aus Textinformationen
    bestehen (beispielsweise dem Namen einer Straße/eines Platzes oder eine genaue Adresse) als auch aus Geodaten.
    Ortsangaben sind auch nicht auf einzelne Positionen beschränkt, sondern können eine Vielzahl von Positionen,
    Flächen, Strecken etc. abdecken.

    see https://oparl.org/spezifikation/online-ansicht/#entity-location

        Attributes:
            id (str):
            description (Union[None, Unset, str]):
            street_address (Union[None, Unset, str]):
            room (Union[None, Unset, str]):
            postal_code (Union[None, Unset, str]):
            sub_locality (Union[None, Unset, str]):
            locality (Union[None, Unset, str]):
            bodies (Union[None, Unset, list[str]]):
            organizations (Union[None, Unset, list[str]]):
            persons (Union[None, Unset, list[str]]):
            meetings (Union[None, Unset, list[str]]):
            papers (Union[None, Unset, list[str]]):
            license_ (Union[None, Unset, str]):
            keyword (Union[None, Unset, list[str]]):
            web (Union[None, Unset, str]):
            geojson (Union['OParlLocationGeojsonType0', None, Unset]):
    """

    id: str
    description: Union[None, Unset, str] = UNSET
    street_address: Union[None, Unset, str] = UNSET
    room: Union[None, Unset, str] = UNSET
    postal_code: Union[None, Unset, str] = UNSET
    sub_locality: Union[None, Unset, str] = UNSET
    locality: Union[None, Unset, str] = UNSET
    bodies: Union[None, Unset, list[str]] = UNSET
    organizations: Union[None, Unset, list[str]] = UNSET
    persons: Union[None, Unset, list[str]] = UNSET
    meetings: Union[None, Unset, list[str]] = UNSET
    papers: Union[None, Unset, list[str]] = UNSET
    license_: Union[None, Unset, str] = UNSET
    keyword: Union[None, Unset, list[str]] = UNSET
    web: Union[None, Unset, str] = UNSET
    geojson: Union["OParlLocationGeojsonType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.o_parl_location_geojson_type_0 import OParlLocationGeojsonType0

        id = self.id

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        street_address: Union[None, Unset, str]
        if isinstance(self.street_address, Unset):
            street_address = UNSET
        else:
            street_address = self.street_address

        room: Union[None, Unset, str]
        if isinstance(self.room, Unset):
            room = UNSET
        else:
            room = self.room

        postal_code: Union[None, Unset, str]
        if isinstance(self.postal_code, Unset):
            postal_code = UNSET
        else:
            postal_code = self.postal_code

        sub_locality: Union[None, Unset, str]
        if isinstance(self.sub_locality, Unset):
            sub_locality = UNSET
        else:
            sub_locality = self.sub_locality

        locality: Union[None, Unset, str]
        if isinstance(self.locality, Unset):
            locality = UNSET
        else:
            locality = self.locality

        bodies: Union[None, Unset, list[str]]
        if isinstance(self.bodies, Unset):
            bodies = UNSET
        elif isinstance(self.bodies, list):
            bodies = self.bodies

        else:
            bodies = self.bodies

        organizations: Union[None, Unset, list[str]]
        if isinstance(self.organizations, Unset):
            organizations = UNSET
        elif isinstance(self.organizations, list):
            organizations = self.organizations

        else:
            organizations = self.organizations

        persons: Union[None, Unset, list[str]]
        if isinstance(self.persons, Unset):
            persons = UNSET
        elif isinstance(self.persons, list):
            persons = self.persons

        else:
            persons = self.persons

        meetings: Union[None, Unset, list[str]]
        if isinstance(self.meetings, Unset):
            meetings = UNSET
        elif isinstance(self.meetings, list):
            meetings = self.meetings

        else:
            meetings = self.meetings

        papers: Union[None, Unset, list[str]]
        if isinstance(self.papers, Unset):
            papers = UNSET
        elif isinstance(self.papers, list):
            papers = self.papers

        else:
            papers = self.papers

        license_: Union[None, Unset, str]
        if isinstance(self.license_, Unset):
            license_ = UNSET
        else:
            license_ = self.license_

        keyword: Union[None, Unset, list[str]]
        if isinstance(self.keyword, Unset):
            keyword = UNSET
        elif isinstance(self.keyword, list):
            keyword = self.keyword

        else:
            keyword = self.keyword

        web: Union[None, Unset, str]
        if isinstance(self.web, Unset):
            web = UNSET
        else:
            web = self.web

        geojson: Union[None, Unset, dict[str, Any]]
        if isinstance(self.geojson, Unset):
            geojson = UNSET
        elif isinstance(self.geojson, OParlLocationGeojsonType0):
            geojson = self.geojson.to_dict()
        else:
            geojson = self.geojson

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if street_address is not UNSET:
            field_dict["streetAddress"] = street_address
        if room is not UNSET:
            field_dict["room"] = room
        if postal_code is not UNSET:
            field_dict["postalCode"] = postal_code
        if sub_locality is not UNSET:
            field_dict["subLocality"] = sub_locality
        if locality is not UNSET:
            field_dict["locality"] = locality
        if bodies is not UNSET:
            field_dict["bodies"] = bodies
        if organizations is not UNSET:
            field_dict["organizations"] = organizations
        if persons is not UNSET:
            field_dict["persons"] = persons
        if meetings is not UNSET:
            field_dict["meetings"] = meetings
        if papers is not UNSET:
            field_dict["papers"] = papers
        if license_ is not UNSET:
            field_dict["license"] = license_
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if web is not UNSET:
            field_dict["web"] = web
        if geojson is not UNSET:
            field_dict["geojson"] = geojson

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.o_parl_location_geojson_type_0 import OParlLocationGeojsonType0

        d = dict(src_dict)
        id = d.pop("id")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_street_address(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        street_address = _parse_street_address(d.pop("streetAddress", UNSET))

        def _parse_room(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        room = _parse_room(d.pop("room", UNSET))

        def _parse_postal_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        postal_code = _parse_postal_code(d.pop("postalCode", UNSET))

        def _parse_sub_locality(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        sub_locality = _parse_sub_locality(d.pop("subLocality", UNSET))

        def _parse_locality(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        locality = _parse_locality(d.pop("locality", UNSET))

        def _parse_bodies(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bodies_type_0 = cast(list[str], data)

                return bodies_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        bodies = _parse_bodies(d.pop("bodies", UNSET))

        def _parse_organizations(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                organizations_type_0 = cast(list[str], data)

                return organizations_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        organizations = _parse_organizations(d.pop("organizations", UNSET))

        def _parse_persons(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                persons_type_0 = cast(list[str], data)

                return persons_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        persons = _parse_persons(d.pop("persons", UNSET))

        def _parse_meetings(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                meetings_type_0 = cast(list[str], data)

                return meetings_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        meetings = _parse_meetings(d.pop("meetings", UNSET))

        def _parse_papers(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                papers_type_0 = cast(list[str], data)

                return papers_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        papers = _parse_papers(d.pop("papers", UNSET))

        def _parse_license_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        license_ = _parse_license_(d.pop("license", UNSET))

        def _parse_keyword(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                keyword_type_0 = cast(list[str], data)

                return keyword_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        keyword = _parse_keyword(d.pop("keyword", UNSET))

        def _parse_web(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        web = _parse_web(d.pop("web", UNSET))

        def _parse_geojson(data: object) -> Union["OParlLocationGeojsonType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                geojson_type_0 = OParlLocationGeojsonType0.from_dict(data)

                return geojson_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlLocationGeojsonType0", None, Unset], data)

        geojson = _parse_geojson(d.pop("geojson", UNSET))

        o_parl_location = cls(
            id=id,
            description=description,
            street_address=street_address,
            room=room,
            postal_code=postal_code,
            sub_locality=sub_locality,
            locality=locality,
            bodies=bodies,
            organizations=organizations,
            persons=persons,
            meetings=meetings,
            papers=papers,
            license_=license_,
            keyword=keyword,
            web=web,
            geojson=geojson,
        )

        o_parl_location.additional_properties = d
        return o_parl_location

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
