from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.organization_list_response_links_type_0 import OrganizationListResponseLinksType0
    from ..models.organization_list_response_pagination_type_0 import OrganizationListResponsePaginationType0
    from ..models.organization_response import OrganizationResponse


T = TypeVar("T", bound="OrganizationListResponse")


@_attrs_define
class OrganizationListResponse:
    """Model for a list of organizations from the OParl API.

    Attributes:
        data (Union[Unset, list['OrganizationResponse']]):
        pagination (Union['OrganizationListResponsePaginationType0', None, Unset]):
        links (Union['OrganizationListResponseLinksType0', None, Unset]):
    """

    data: Union[Unset, list["OrganizationResponse"]] = UNSET
    pagination: Union["OrganizationListResponsePaginationType0", None, Unset] = UNSET
    links: Union["OrganizationListResponseLinksType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.organization_list_response_links_type_0 import OrganizationListResponseLinksType0
        from ..models.organization_list_response_pagination_type_0 import OrganizationListResponsePaginationType0

        data: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        pagination: Union[None, Unset, dict[str, Any]]
        if isinstance(self.pagination, Unset):
            pagination = UNSET
        elif isinstance(self.pagination, OrganizationListResponsePaginationType0):
            pagination = self.pagination.to_dict()
        else:
            pagination = self.pagination

        links: Union[None, Unset, dict[str, Any]]
        if isinstance(self.links, Unset):
            links = UNSET
        elif isinstance(self.links, OrganizationListResponseLinksType0):
            links = self.links.to_dict()
        else:
            links = self.links

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if links is not UNSET:
            field_dict["links"] = links

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.organization_list_response_links_type_0 import OrganizationListResponseLinksType0
        from ..models.organization_list_response_pagination_type_0 import OrganizationListResponsePaginationType0
        from ..models.organization_response import OrganizationResponse

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = OrganizationResponse.from_dict(data_item_data)

            data.append(data_item)

        def _parse_pagination(data: object) -> Union["OrganizationListResponsePaginationType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                pagination_type_0 = OrganizationListResponsePaginationType0.from_dict(data)

                return pagination_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OrganizationListResponsePaginationType0", None, Unset], data)

        pagination = _parse_pagination(d.pop("pagination", UNSET))

        def _parse_links(data: object) -> Union["OrganizationListResponseLinksType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                links_type_0 = OrganizationListResponseLinksType0.from_dict(data)

                return links_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OrganizationListResponseLinksType0", None, Unset], data)

        links = _parse_links(d.pop("links", UNSET))

        organization_list_response = cls(
            data=data,
            pagination=pagination,
            links=links,
        )

        organization_list_response.additional_properties = d
        return organization_list_response

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
