import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.meeting import Meeting
    from ..models.organization import Organization
    from ..models.paper import Paper


T = TypeVar("T", bound="Consultation")


@_attrs_define
class Consultation:
    """Der Objekttyp oparl:Consultation dient dazu, die Beratung einer Drucksache (oparl:Paper) in einer Sitzung
    abzubilden. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit stattgefunden hat oder diese
    für die Zukunft geplant ist. Die Gesamtheit aller Objekte des Typs oparl:Consultation zu einer bestimmten
    Drucksache bildet das ab, was in der Praxis als “Beratungsfolge” der Drucksache bezeichnet wird.

        Attributes:
            id (UUID):
            id_ref (str):
            role (Union[None, str]):
            created (Union[None, Unset, datetime.datetime]):
            modified (Union[None, Unset, datetime.datetime]):
            deleted (Union[Unset, bool]):  Default: False.
            bi (Union[Unset, int]):  Default: 0.
            type_ (Union[Unset, str]):  Default: 'https://schema.oparl.org/1.1/Consultation'.
            authoritative (Union[Unset, bool]):  Default: True.
            license_ (Union[None, Unset, str]):
            keyword (Union[None, Unset, list[str]]):
            web (Union[None, Unset, str]):
            paper (Union['Paper', None, Unset]):
            meeting (Union['Meeting', None, Unset]):
            paper_ref (Union[None, Unset, str]):
            meeting_ref (Union[None, Unset, str]):
            organizations (Union[Unset, list['Organization']]):
            organization_ref (Union[None, Unset, list[str]]):
    """

    id: UUID
    id_ref: str
    role: Union[None, str]
    created: Union[None, Unset, datetime.datetime] = UNSET
    modified: Union[None, Unset, datetime.datetime] = UNSET
    deleted: Union[Unset, bool] = False
    bi: Union[Unset, int] = 0
    type_: Union[Unset, str] = "https://schema.oparl.org/1.1/Consultation"
    authoritative: Union[Unset, bool] = True
    license_: Union[None, Unset, str] = UNSET
    keyword: Union[None, Unset, list[str]] = UNSET
    web: Union[None, Unset, str] = UNSET
    paper: Union["Paper", None, Unset] = UNSET
    meeting: Union["Meeting", None, Unset] = UNSET
    paper_ref: Union[None, Unset, str] = UNSET
    meeting_ref: Union[None, Unset, str] = UNSET
    organizations: Union[Unset, list["Organization"]] = UNSET
    organization_ref: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.meeting import Meeting
        from ..models.paper import Paper

        id = str(self.id)

        id_ref = self.id_ref

        role: Union[None, str]
        role = self.role

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

        bi = self.bi

        type_ = self.type_

        authoritative = self.authoritative

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

        paper: Union[None, Unset, dict[str, Any]]
        if isinstance(self.paper, Unset):
            paper = UNSET
        elif isinstance(self.paper, Paper):
            paper = self.paper.to_dict()
        else:
            paper = self.paper

        meeting: Union[None, Unset, dict[str, Any]]
        if isinstance(self.meeting, Unset):
            meeting = UNSET
        elif isinstance(self.meeting, Meeting):
            meeting = self.meeting.to_dict()
        else:
            meeting = self.meeting

        paper_ref: Union[None, Unset, str]
        if isinstance(self.paper_ref, Unset):
            paper_ref = UNSET
        else:
            paper_ref = self.paper_ref

        meeting_ref: Union[None, Unset, str]
        if isinstance(self.meeting_ref, Unset):
            meeting_ref = UNSET
        else:
            meeting_ref = self.meeting_ref

        organizations: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.organizations, Unset):
            organizations = []
            for organizations_item_data in self.organizations:
                organizations_item = organizations_item_data.to_dict()
                organizations.append(organizations_item)

        organization_ref: Union[None, Unset, list[str]]
        if isinstance(self.organization_ref, Unset):
            organization_ref = UNSET
        elif isinstance(self.organization_ref, list):
            organization_ref = self.organization_ref

        else:
            organization_ref = self.organization_ref

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "id_ref": id_ref,
                "role": role,
            }
        )
        if created is not UNSET:
            field_dict["created"] = created
        if modified is not UNSET:
            field_dict["modified"] = modified
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if bi is not UNSET:
            field_dict["bi"] = bi
        if type_ is not UNSET:
            field_dict["type"] = type_
        if authoritative is not UNSET:
            field_dict["authoritative"] = authoritative
        if license_ is not UNSET:
            field_dict["license"] = license_
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if web is not UNSET:
            field_dict["web"] = web
        if paper is not UNSET:
            field_dict["paper"] = paper
        if meeting is not UNSET:
            field_dict["meeting"] = meeting
        if paper_ref is not UNSET:
            field_dict["paper_ref"] = paper_ref
        if meeting_ref is not UNSET:
            field_dict["meeting_ref"] = meeting_ref
        if organizations is not UNSET:
            field_dict["organizations"] = organizations
        if organization_ref is not UNSET:
            field_dict["organization_ref"] = organization_ref

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.meeting import Meeting
        from ..models.organization import Organization
        from ..models.paper import Paper

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        id_ref = d.pop("id_ref")

        def _parse_role(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        role = _parse_role(d.pop("role"))

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

        bi = d.pop("bi", UNSET)

        type_ = d.pop("type", UNSET)

        authoritative = d.pop("authoritative", UNSET)

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

        def _parse_paper(data: object) -> Union["Paper", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                paper_type_0 = Paper.from_dict(data)

                return paper_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Paper", None, Unset], data)

        paper = _parse_paper(d.pop("paper", UNSET))

        def _parse_meeting(data: object) -> Union["Meeting", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                meeting_type_0 = Meeting.from_dict(data)

                return meeting_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Meeting", None, Unset], data)

        meeting = _parse_meeting(d.pop("meeting", UNSET))

        def _parse_paper_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        paper_ref = _parse_paper_ref(d.pop("paper_ref", UNSET))

        def _parse_meeting_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        meeting_ref = _parse_meeting_ref(d.pop("meeting_ref", UNSET))

        organizations = []
        _organizations = d.pop("organizations", UNSET)
        for organizations_item_data in _organizations or []:
            organizations_item = Organization.from_dict(organizations_item_data)

            organizations.append(organizations_item)

        def _parse_organization_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                organization_ref_type_0 = cast(list[str], data)

                return organization_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        organization_ref = _parse_organization_ref(d.pop("organization_ref", UNSET))

        consultation = cls(
            id=id,
            id_ref=id_ref,
            role=role,
            created=created,
            modified=modified,
            deleted=deleted,
            bi=bi,
            type_=type_,
            authoritative=authoritative,
            license_=license_,
            keyword=keyword,
            web=web,
            paper=paper,
            meeting=meeting,
            paper_ref=paper_ref,
            meeting_ref=meeting_ref,
            organizations=organizations,
            organization_ref=organization_ref,
        )

        consultation.additional_properties = d
        return consultation

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
