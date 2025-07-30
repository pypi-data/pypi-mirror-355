import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.o_parl_agenda_item import OParlAgendaItem
    from ..models.o_parl_file import OParlFile
    from ..models.o_parl_location import OParlLocation
    from ..models.organization import Organization
    from ..models.person import Person


T = TypeVar("T", bound="Meeting")


@_attrs_define
class Meeting:
    """Dieser Objekttyp dient der Abbildung von Sitzungen in der parlamentarischen Arbeit. Sitzungen sind formelle
    Zusammenkünfte von Gruppierungen zu einem bestimmten Zeitpunkt an einem bestimmten Ort. Sie können
    Tagesordnungspunkte
    enthalten, die wiederum Drucksachen (oparl:Paper) behandeln. Sitzungen können öffentlich oder nicht-öffentlich sein
    und
    können verschiedene Status haben, wie geplant, verschoben, abgesagt oder abgeschlossen.

    Siehe https://oparl.org/spezifikation/online-ansicht/#entity-meeting

        Attributes:
            id (UUID):
            id_ref (str):
            name (str):
            meeting_state (str):
            cancelled (Union[None, Unset, bool]):  Default: False.
            start (Union[None, Unset, datetime.datetime]):
            end (Union[None, Unset, datetime.datetime]):
            location (Union['OParlLocation', None, Unset]):
            organization (Union[None, Unset, list['Organization']]):
            participants (Union[None, Unset, list['Person']]):
            invitation (Union['OParlFile', None, Unset]):
            results_protocol (Union['OParlFile', None, Unset]):
            verbatim_protocol (Union['OParlFile', None, Unset]):
            auxiliary_file (Union[None, Unset, list['OParlFile']]):
            agenda_item (Union[None, Unset, list['OParlAgendaItem']]):
            license_ (Union[None, Unset, str]):
            keyword (Union[None, Unset, list[str]]):
            web (Union[None, Unset, str]):
    """

    id: UUID
    id_ref: str
    name: str
    meeting_state: str
    cancelled: Union[None, Unset, bool] = False
    start: Union[None, Unset, datetime.datetime] = UNSET
    end: Union[None, Unset, datetime.datetime] = UNSET
    location: Union["OParlLocation", None, Unset] = UNSET
    organization: Union[None, Unset, list["Organization"]] = UNSET
    participants: Union[None, Unset, list["Person"]] = UNSET
    invitation: Union["OParlFile", None, Unset] = UNSET
    results_protocol: Union["OParlFile", None, Unset] = UNSET
    verbatim_protocol: Union["OParlFile", None, Unset] = UNSET
    auxiliary_file: Union[None, Unset, list["OParlFile"]] = UNSET
    agenda_item: Union[None, Unset, list["OParlAgendaItem"]] = UNSET
    license_: Union[None, Unset, str] = UNSET
    keyword: Union[None, Unset, list[str]] = UNSET
    web: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.o_parl_file import OParlFile
        from ..models.o_parl_location import OParlLocation

        id = str(self.id)

        id_ref = self.id_ref

        name = self.name

        meeting_state = self.meeting_state

        cancelled: Union[None, Unset, bool]
        if isinstance(self.cancelled, Unset):
            cancelled = UNSET
        else:
            cancelled = self.cancelled

        start: Union[None, Unset, str]
        if isinstance(self.start, Unset):
            start = UNSET
        elif isinstance(self.start, datetime.datetime):
            start = self.start.isoformat()
        else:
            start = self.start

        end: Union[None, Unset, str]
        if isinstance(self.end, Unset):
            end = UNSET
        elif isinstance(self.end, datetime.datetime):
            end = self.end.isoformat()
        else:
            end = self.end

        location: Union[None, Unset, dict[str, Any]]
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, OParlLocation):
            location = self.location.to_dict()
        else:
            location = self.location

        organization: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, list):
            organization = []
            for organization_type_0_item_data in self.organization:
                organization_type_0_item = organization_type_0_item_data.to_dict()
                organization.append(organization_type_0_item)

        else:
            organization = self.organization

        participants: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.participants, Unset):
            participants = UNSET
        elif isinstance(self.participants, list):
            participants = []
            for participants_type_0_item_data in self.participants:
                participants_type_0_item = participants_type_0_item_data.to_dict()
                participants.append(participants_type_0_item)

        else:
            participants = self.participants

        invitation: Union[None, Unset, dict[str, Any]]
        if isinstance(self.invitation, Unset):
            invitation = UNSET
        elif isinstance(self.invitation, OParlFile):
            invitation = self.invitation.to_dict()
        else:
            invitation = self.invitation

        results_protocol: Union[None, Unset, dict[str, Any]]
        if isinstance(self.results_protocol, Unset):
            results_protocol = UNSET
        elif isinstance(self.results_protocol, OParlFile):
            results_protocol = self.results_protocol.to_dict()
        else:
            results_protocol = self.results_protocol

        verbatim_protocol: Union[None, Unset, dict[str, Any]]
        if isinstance(self.verbatim_protocol, Unset):
            verbatim_protocol = UNSET
        elif isinstance(self.verbatim_protocol, OParlFile):
            verbatim_protocol = self.verbatim_protocol.to_dict()
        else:
            verbatim_protocol = self.verbatim_protocol

        auxiliary_file: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.auxiliary_file, Unset):
            auxiliary_file = UNSET
        elif isinstance(self.auxiliary_file, list):
            auxiliary_file = []
            for auxiliary_file_type_0_item_data in self.auxiliary_file:
                auxiliary_file_type_0_item = auxiliary_file_type_0_item_data.to_dict()
                auxiliary_file.append(auxiliary_file_type_0_item)

        else:
            auxiliary_file = self.auxiliary_file

        agenda_item: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.agenda_item, Unset):
            agenda_item = UNSET
        elif isinstance(self.agenda_item, list):
            agenda_item = []
            for agenda_item_type_0_item_data in self.agenda_item:
                agenda_item_type_0_item = agenda_item_type_0_item_data.to_dict()
                agenda_item.append(agenda_item_type_0_item)

        else:
            agenda_item = self.agenda_item

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "id_ref": id_ref,
                "name": name,
                "meetingState": meeting_state,
            }
        )
        if cancelled is not UNSET:
            field_dict["cancelled"] = cancelled
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if location is not UNSET:
            field_dict["location"] = location
        if organization is not UNSET:
            field_dict["organization"] = organization
        if participants is not UNSET:
            field_dict["participants"] = participants
        if invitation is not UNSET:
            field_dict["invitation"] = invitation
        if results_protocol is not UNSET:
            field_dict["resultsProtocol"] = results_protocol
        if verbatim_protocol is not UNSET:
            field_dict["verbatimProtocol"] = verbatim_protocol
        if auxiliary_file is not UNSET:
            field_dict["auxiliaryFile"] = auxiliary_file
        if agenda_item is not UNSET:
            field_dict["agendaItem"] = agenda_item
        if license_ is not UNSET:
            field_dict["license"] = license_
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if web is not UNSET:
            field_dict["web"] = web

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.o_parl_agenda_item import OParlAgendaItem
        from ..models.o_parl_file import OParlFile
        from ..models.o_parl_location import OParlLocation
        from ..models.organization import Organization
        from ..models.person import Person

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        id_ref = d.pop("id_ref")

        name = d.pop("name")

        meeting_state = d.pop("meetingState")

        def _parse_cancelled(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        cancelled = _parse_cancelled(d.pop("cancelled", UNSET))

        def _parse_start(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_type_0 = isoparse(data)

                return start_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        start = _parse_start(d.pop("start", UNSET))

        def _parse_end(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_type_0 = isoparse(data)

                return end_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        end = _parse_end(d.pop("end", UNSET))

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

        def _parse_organization(data: object) -> Union[None, Unset, list["Organization"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                organization_type_0 = []
                _organization_type_0 = data
                for organization_type_0_item_data in _organization_type_0:
                    organization_type_0_item = Organization.from_dict(organization_type_0_item_data)

                    organization_type_0.append(organization_type_0_item)

                return organization_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Organization"]], data)

        organization = _parse_organization(d.pop("organization", UNSET))

        def _parse_participants(data: object) -> Union[None, Unset, list["Person"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                participants_type_0 = []
                _participants_type_0 = data
                for participants_type_0_item_data in _participants_type_0:
                    participants_type_0_item = Person.from_dict(participants_type_0_item_data)

                    participants_type_0.append(participants_type_0_item)

                return participants_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Person"]], data)

        participants = _parse_participants(d.pop("participants", UNSET))

        def _parse_invitation(data: object) -> Union["OParlFile", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                invitation_type_0 = OParlFile.from_dict(data)

                return invitation_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlFile", None, Unset], data)

        invitation = _parse_invitation(d.pop("invitation", UNSET))

        def _parse_results_protocol(data: object) -> Union["OParlFile", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                results_protocol_type_0 = OParlFile.from_dict(data)

                return results_protocol_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlFile", None, Unset], data)

        results_protocol = _parse_results_protocol(d.pop("resultsProtocol", UNSET))

        def _parse_verbatim_protocol(data: object) -> Union["OParlFile", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                verbatim_protocol_type_0 = OParlFile.from_dict(data)

                return verbatim_protocol_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlFile", None, Unset], data)

        verbatim_protocol = _parse_verbatim_protocol(d.pop("verbatimProtocol", UNSET))

        def _parse_auxiliary_file(data: object) -> Union[None, Unset, list["OParlFile"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                auxiliary_file_type_0 = []
                _auxiliary_file_type_0 = data
                for auxiliary_file_type_0_item_data in _auxiliary_file_type_0:
                    auxiliary_file_type_0_item = OParlFile.from_dict(auxiliary_file_type_0_item_data)

                    auxiliary_file_type_0.append(auxiliary_file_type_0_item)

                return auxiliary_file_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["OParlFile"]], data)

        auxiliary_file = _parse_auxiliary_file(d.pop("auxiliaryFile", UNSET))

        def _parse_agenda_item(data: object) -> Union[None, Unset, list["OParlAgendaItem"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                agenda_item_type_0 = []
                _agenda_item_type_0 = data
                for agenda_item_type_0_item_data in _agenda_item_type_0:
                    agenda_item_type_0_item = OParlAgendaItem.from_dict(agenda_item_type_0_item_data)

                    agenda_item_type_0.append(agenda_item_type_0_item)

                return agenda_item_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["OParlAgendaItem"]], data)

        agenda_item = _parse_agenda_item(d.pop("agendaItem", UNSET))

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

        meeting = cls(
            id=id,
            id_ref=id_ref,
            name=name,
            meeting_state=meeting_state,
            cancelled=cancelled,
            start=start,
            end=end,
            location=location,
            organization=organization,
            participants=participants,
            invitation=invitation,
            results_protocol=results_protocol,
            verbatim_protocol=verbatim_protocol,
            auxiliary_file=auxiliary_file,
            agenda_item=agenda_item,
            license_=license_,
            keyword=keyword,
            web=web,
        )

        meeting.additional_properties = d
        return meeting

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
