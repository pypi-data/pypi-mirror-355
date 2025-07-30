import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SystemResponse")


@_attrs_define
class SystemResponse:
    """Model for the system response from the OParl API.

    Attributes:
        license_ (Union[None, str]):
        body (str):
        name (str):
        created (Union[None, Unset, datetime.datetime]):
        modified (Union[None, Unset, datetime.datetime]):
        deleted (Union[Unset, bool]):  Default: False.
        type_ (Union[Unset, str]):  Default: 'https://schema.oparl.org/1.1/System'.
        oparl_version (Union[Unset, str]):  Default: 'https://schema.oparl.org/1.1/'.
        other_oparl_versions (Union[None, Unset, list[str]]):
        contact_email (Union[None, Unset, str]):
        contact_name (Union[None, Unset, str]):
        website (Union[None, Unset, str]):
        vendor (Union[Unset, str]):  Default: 'Mach! Den! Staat!'.
        product (Union[Unset, str]):  Default: 'Stadt Bonn OParl API Cache'.
    """

    license_: Union[None, str]
    body: str
    name: str
    created: Union[None, Unset, datetime.datetime] = UNSET
    modified: Union[None, Unset, datetime.datetime] = UNSET
    deleted: Union[Unset, bool] = False
    type_: Union[Unset, str] = "https://schema.oparl.org/1.1/System"
    oparl_version: Union[Unset, str] = "https://schema.oparl.org/1.1/"
    other_oparl_versions: Union[None, Unset, list[str]] = UNSET
    contact_email: Union[None, Unset, str] = UNSET
    contact_name: Union[None, Unset, str] = UNSET
    website: Union[None, Unset, str] = UNSET
    vendor: Union[Unset, str] = "Mach! Den! Staat!"
    product: Union[Unset, str] = "Stadt Bonn OParl API Cache"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        license_: Union[None, str]
        license_ = self.license_

        body = self.body

        name = self.name

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

        oparl_version = self.oparl_version

        other_oparl_versions: Union[None, Unset, list[str]]
        if isinstance(self.other_oparl_versions, Unset):
            other_oparl_versions = UNSET
        elif isinstance(self.other_oparl_versions, list):
            other_oparl_versions = self.other_oparl_versions

        else:
            other_oparl_versions = self.other_oparl_versions

        contact_email: Union[None, Unset, str]
        if isinstance(self.contact_email, Unset):
            contact_email = UNSET
        else:
            contact_email = self.contact_email

        contact_name: Union[None, Unset, str]
        if isinstance(self.contact_name, Unset):
            contact_name = UNSET
        else:
            contact_name = self.contact_name

        website: Union[None, Unset, str]
        if isinstance(self.website, Unset):
            website = UNSET
        else:
            website = self.website

        vendor = self.vendor

        product = self.product

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "license": license_,
                "body": body,
                "name": name,
            }
        )
        if created is not UNSET:
            field_dict["created"] = created
        if modified is not UNSET:
            field_dict["modified"] = modified
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if type_ is not UNSET:
            field_dict["type"] = type_
        if oparl_version is not UNSET:
            field_dict["oparlVersion"] = oparl_version
        if other_oparl_versions is not UNSET:
            field_dict["otherOparlVersions"] = other_oparl_versions
        if contact_email is not UNSET:
            field_dict["contactEmail"] = contact_email
        if contact_name is not UNSET:
            field_dict["contactName"] = contact_name
        if website is not UNSET:
            field_dict["website"] = website
        if vendor is not UNSET:
            field_dict["vendor"] = vendor
        if product is not UNSET:
            field_dict["product"] = product

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_license_(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        license_ = _parse_license_(d.pop("license"))

        body = d.pop("body")

        name = d.pop("name")

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

        oparl_version = d.pop("oparlVersion", UNSET)

        def _parse_other_oparl_versions(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                other_oparl_versions_type_0 = cast(list[str], data)

                return other_oparl_versions_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        other_oparl_versions = _parse_other_oparl_versions(d.pop("otherOparlVersions", UNSET))

        def _parse_contact_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        contact_email = _parse_contact_email(d.pop("contactEmail", UNSET))

        def _parse_contact_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        contact_name = _parse_contact_name(d.pop("contactName", UNSET))

        def _parse_website(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        website = _parse_website(d.pop("website", UNSET))

        vendor = d.pop("vendor", UNSET)

        product = d.pop("product", UNSET)

        system_response = cls(
            license_=license_,
            body=body,
            name=name,
            created=created,
            modified=modified,
            deleted=deleted,
            type_=type_,
            oparl_version=oparl_version,
            other_oparl_versions=other_oparl_versions,
            contact_email=contact_email,
            contact_name=contact_name,
            website=website,
            vendor=vendor,
            product=product,
        )

        system_response.additional_properties = d
        return system_response

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
