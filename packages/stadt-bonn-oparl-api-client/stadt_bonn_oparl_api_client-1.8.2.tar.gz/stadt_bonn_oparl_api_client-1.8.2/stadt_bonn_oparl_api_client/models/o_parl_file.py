import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="OParlFile")


@_attrs_define
class OParlFile:
    """Model for a file in the OParl API.

    Attributes:
        id (str):
        name (str):
        access_url (str):
        file_name (Union[None, Unset, str]):
        mime_type (Union[None, Unset, str]):
        date (Union[None, Unset, datetime.datetime]):
        size (Union[None, Unset, int]):
        sha_1_checksum (Union[None, Unset, str]):
        sha_512_checksum (Union[None, Unset, str]):
        text (Union[None, Unset, str]):
        download_url (Union[None, Unset, str]):
        file_license (Union[None, Unset, str]):
        meeting (Union[None, Unset, list[str]]):
        agenda_item (Union[None, Unset, list[str]]):
        paper (Union[None, Unset, list[str]]):
        license_ (Union[None, Unset, str]):
        keyword (Union[None, Unset, list[str]]):
        web (Union[None, Unset, str]):
    """

    id: str
    name: str
    access_url: str
    file_name: Union[None, Unset, str] = UNSET
    mime_type: Union[None, Unset, str] = UNSET
    date: Union[None, Unset, datetime.datetime] = UNSET
    size: Union[None, Unset, int] = UNSET
    sha_1_checksum: Union[None, Unset, str] = UNSET
    sha_512_checksum: Union[None, Unset, str] = UNSET
    text: Union[None, Unset, str] = UNSET
    download_url: Union[None, Unset, str] = UNSET
    file_license: Union[None, Unset, str] = UNSET
    meeting: Union[None, Unset, list[str]] = UNSET
    agenda_item: Union[None, Unset, list[str]] = UNSET
    paper: Union[None, Unset, list[str]] = UNSET
    license_: Union[None, Unset, str] = UNSET
    keyword: Union[None, Unset, list[str]] = UNSET
    web: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        access_url = self.access_url

        file_name: Union[None, Unset, str]
        if isinstance(self.file_name, Unset):
            file_name = UNSET
        else:
            file_name = self.file_name

        mime_type: Union[None, Unset, str]
        if isinstance(self.mime_type, Unset):
            mime_type = UNSET
        else:
            mime_type = self.mime_type

        date: Union[None, Unset, str]
        if isinstance(self.date, Unset):
            date = UNSET
        elif isinstance(self.date, datetime.datetime):
            date = self.date.isoformat()
        else:
            date = self.date

        size: Union[None, Unset, int]
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        sha_1_checksum: Union[None, Unset, str]
        if isinstance(self.sha_1_checksum, Unset):
            sha_1_checksum = UNSET
        else:
            sha_1_checksum = self.sha_1_checksum

        sha_512_checksum: Union[None, Unset, str]
        if isinstance(self.sha_512_checksum, Unset):
            sha_512_checksum = UNSET
        else:
            sha_512_checksum = self.sha_512_checksum

        text: Union[None, Unset, str]
        if isinstance(self.text, Unset):
            text = UNSET
        else:
            text = self.text

        download_url: Union[None, Unset, str]
        if isinstance(self.download_url, Unset):
            download_url = UNSET
        else:
            download_url = self.download_url

        file_license: Union[None, Unset, str]
        if isinstance(self.file_license, Unset):
            file_license = UNSET
        else:
            file_license = self.file_license

        meeting: Union[None, Unset, list[str]]
        if isinstance(self.meeting, Unset):
            meeting = UNSET
        elif isinstance(self.meeting, list):
            meeting = self.meeting

        else:
            meeting = self.meeting

        agenda_item: Union[None, Unset, list[str]]
        if isinstance(self.agenda_item, Unset):
            agenda_item = UNSET
        elif isinstance(self.agenda_item, list):
            agenda_item = self.agenda_item

        else:
            agenda_item = self.agenda_item

        paper: Union[None, Unset, list[str]]
        if isinstance(self.paper, Unset):
            paper = UNSET
        elif isinstance(self.paper, list):
            paper = self.paper

        else:
            paper = self.paper

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
                "name": name,
                "accessUrl": access_url,
            }
        )
        if file_name is not UNSET:
            field_dict["fileName"] = file_name
        if mime_type is not UNSET:
            field_dict["mimeType"] = mime_type
        if date is not UNSET:
            field_dict["date"] = date
        if size is not UNSET:
            field_dict["size"] = size
        if sha_1_checksum is not UNSET:
            field_dict["sha1Checksum"] = sha_1_checksum
        if sha_512_checksum is not UNSET:
            field_dict["sha512Checksum"] = sha_512_checksum
        if text is not UNSET:
            field_dict["text"] = text
        if download_url is not UNSET:
            field_dict["downloadUrl"] = download_url
        if file_license is not UNSET:
            field_dict["fileLicense"] = file_license
        if meeting is not UNSET:
            field_dict["meeting"] = meeting
        if agenda_item is not UNSET:
            field_dict["agendaItem"] = agenda_item
        if paper is not UNSET:
            field_dict["paper"] = paper
        if license_ is not UNSET:
            field_dict["license"] = license_
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if web is not UNSET:
            field_dict["web"] = web

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        access_url = d.pop("accessUrl")

        def _parse_file_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        file_name = _parse_file_name(d.pop("fileName", UNSET))

        def _parse_mime_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        mime_type = _parse_mime_type(d.pop("mimeType", UNSET))

        def _parse_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                date_type_0 = isoparse(data)

                return date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        date = _parse_date(d.pop("date", UNSET))

        def _parse_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        size = _parse_size(d.pop("size", UNSET))

        def _parse_sha_1_checksum(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        sha_1_checksum = _parse_sha_1_checksum(d.pop("sha1Checksum", UNSET))

        def _parse_sha_512_checksum(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        sha_512_checksum = _parse_sha_512_checksum(d.pop("sha512Checksum", UNSET))

        def _parse_text(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        text = _parse_text(d.pop("text", UNSET))

        def _parse_download_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        download_url = _parse_download_url(d.pop("downloadUrl", UNSET))

        def _parse_file_license(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        file_license = _parse_file_license(d.pop("fileLicense", UNSET))

        def _parse_meeting(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                meeting_type_0 = cast(list[str], data)

                return meeting_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        meeting = _parse_meeting(d.pop("meeting", UNSET))

        def _parse_agenda_item(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                agenda_item_type_0 = cast(list[str], data)

                return agenda_item_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        agenda_item = _parse_agenda_item(d.pop("agendaItem", UNSET))

        def _parse_paper(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                paper_type_0 = cast(list[str], data)

                return paper_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        paper = _parse_paper(d.pop("paper", UNSET))

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

        o_parl_file = cls(
            id=id,
            name=name,
            access_url=access_url,
            file_name=file_name,
            mime_type=mime_type,
            date=date,
            size=size,
            sha_1_checksum=sha_1_checksum,
            sha_512_checksum=sha_512_checksum,
            text=text,
            download_url=download_url,
            file_license=file_license,
            meeting=meeting,
            agenda_item=agenda_item,
            paper=paper,
            license_=license_,
            keyword=keyword,
            web=web,
        )

        o_parl_file.additional_properties = d
        return o_parl_file

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
