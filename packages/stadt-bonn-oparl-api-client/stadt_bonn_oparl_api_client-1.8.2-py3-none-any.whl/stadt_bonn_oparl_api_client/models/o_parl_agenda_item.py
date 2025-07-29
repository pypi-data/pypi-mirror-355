import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.o_parl_agenda_item_auxiliary_file_type_0_item import OParlAgendaItemAuxiliaryFileType0Item
    from ..models.o_parl_agenda_item_resolution_file_type_0 import OParlAgendaItemResolutionFileType0


T = TypeVar("T", bound="OParlAgendaItem")


@_attrs_define
class OParlAgendaItem:
    """
    Attributes:
        id (str):
        number (Union[None, str]):
        order (int):
        meeting (Union[None, Unset, str]):
        name (Union[None, Unset, str]):
        public (Union[None, Unset, bool]):  Default: True.
        consultation (Union[None, Unset, str]):
        result (Union[None, Unset, str]):
        resolution_text (Union[None, Unset, str]):
        resolution_file (Union['OParlAgendaItemResolutionFileType0', None, Unset]):
        auxiliary_file (Union[None, Unset, list['OParlAgendaItemAuxiliaryFileType0Item']]):
        start (Union[None, Unset, datetime.datetime]):
        end (Union[None, Unset, datetime.datetime]):
        license_ (Union[None, Unset, str]):
        keyword (Union[None, Unset, list[str]]):
        web (Union[None, Unset, str]):
    """

    id: str
    number: Union[None, str]
    order: int
    meeting: Union[None, Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    public: Union[None, Unset, bool] = True
    consultation: Union[None, Unset, str] = UNSET
    result: Union[None, Unset, str] = UNSET
    resolution_text: Union[None, Unset, str] = UNSET
    resolution_file: Union["OParlAgendaItemResolutionFileType0", None, Unset] = UNSET
    auxiliary_file: Union[None, Unset, list["OParlAgendaItemAuxiliaryFileType0Item"]] = UNSET
    start: Union[None, Unset, datetime.datetime] = UNSET
    end: Union[None, Unset, datetime.datetime] = UNSET
    license_: Union[None, Unset, str] = UNSET
    keyword: Union[None, Unset, list[str]] = UNSET
    web: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.o_parl_agenda_item_resolution_file_type_0 import OParlAgendaItemResolutionFileType0

        id = self.id

        number: Union[None, str]
        number = self.number

        order = self.order

        meeting: Union[None, Unset, str]
        if isinstance(self.meeting, Unset):
            meeting = UNSET
        else:
            meeting = self.meeting

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        public: Union[None, Unset, bool]
        if isinstance(self.public, Unset):
            public = UNSET
        else:
            public = self.public

        consultation: Union[None, Unset, str]
        if isinstance(self.consultation, Unset):
            consultation = UNSET
        else:
            consultation = self.consultation

        result: Union[None, Unset, str]
        if isinstance(self.result, Unset):
            result = UNSET
        else:
            result = self.result

        resolution_text: Union[None, Unset, str]
        if isinstance(self.resolution_text, Unset):
            resolution_text = UNSET
        else:
            resolution_text = self.resolution_text

        resolution_file: Union[None, Unset, dict[str, Any]]
        if isinstance(self.resolution_file, Unset):
            resolution_file = UNSET
        elif isinstance(self.resolution_file, OParlAgendaItemResolutionFileType0):
            resolution_file = self.resolution_file.to_dict()
        else:
            resolution_file = self.resolution_file

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
                "number": number,
                "order": order,
            }
        )
        if meeting is not UNSET:
            field_dict["meeting"] = meeting
        if name is not UNSET:
            field_dict["name"] = name
        if public is not UNSET:
            field_dict["public"] = public
        if consultation is not UNSET:
            field_dict["consultation"] = consultation
        if result is not UNSET:
            field_dict["result"] = result
        if resolution_text is not UNSET:
            field_dict["resolutionText"] = resolution_text
        if resolution_file is not UNSET:
            field_dict["resolutionFile"] = resolution_file
        if auxiliary_file is not UNSET:
            field_dict["auxiliaryFile"] = auxiliary_file
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if license_ is not UNSET:
            field_dict["license"] = license_
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if web is not UNSET:
            field_dict["web"] = web

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.o_parl_agenda_item_auxiliary_file_type_0_item import OParlAgendaItemAuxiliaryFileType0Item
        from ..models.o_parl_agenda_item_resolution_file_type_0 import OParlAgendaItemResolutionFileType0

        d = dict(src_dict)
        id = d.pop("id")

        def _parse_number(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        number = _parse_number(d.pop("number"))

        order = d.pop("order")

        def _parse_meeting(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        meeting = _parse_meeting(d.pop("meeting", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_public(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        public = _parse_public(d.pop("public", UNSET))

        def _parse_consultation(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        consultation = _parse_consultation(d.pop("consultation", UNSET))

        def _parse_result(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        result = _parse_result(d.pop("result", UNSET))

        def _parse_resolution_text(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        resolution_text = _parse_resolution_text(d.pop("resolutionText", UNSET))

        def _parse_resolution_file(data: object) -> Union["OParlAgendaItemResolutionFileType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                resolution_file_type_0 = OParlAgendaItemResolutionFileType0.from_dict(data)

                return resolution_file_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlAgendaItemResolutionFileType0", None, Unset], data)

        resolution_file = _parse_resolution_file(d.pop("resolutionFile", UNSET))

        def _parse_auxiliary_file(data: object) -> Union[None, Unset, list["OParlAgendaItemAuxiliaryFileType0Item"]]:
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
                    auxiliary_file_type_0_item = OParlAgendaItemAuxiliaryFileType0Item.from_dict(
                        auxiliary_file_type_0_item_data
                    )

                    auxiliary_file_type_0.append(auxiliary_file_type_0_item)

                return auxiliary_file_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["OParlAgendaItemAuxiliaryFileType0Item"]], data)

        auxiliary_file = _parse_auxiliary_file(d.pop("auxiliaryFile", UNSET))

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

        o_parl_agenda_item = cls(
            id=id,
            number=number,
            order=order,
            meeting=meeting,
            name=name,
            public=public,
            consultation=consultation,
            result=result,
            resolution_text=resolution_text,
            resolution_file=resolution_file,
            auxiliary_file=auxiliary_file,
            start=start,
            end=end,
            license_=license_,
            keyword=keyword,
            web=web,
        )

        o_parl_agenda_item.additional_properties = d
        return o_parl_agenda_item

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
