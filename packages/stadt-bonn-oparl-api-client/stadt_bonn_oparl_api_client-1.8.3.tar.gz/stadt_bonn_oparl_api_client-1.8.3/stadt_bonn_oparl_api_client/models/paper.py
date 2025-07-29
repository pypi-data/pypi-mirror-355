import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.o_parl_file import OParlFile
    from ..models.o_parl_location import OParlLocation
    from ..models.organization import Organization
    from ..models.person import Person


T = TypeVar("T", bound="Paper")


@_attrs_define
class Paper:
    """Dieser Objekttyp dient der Abbildung von Drucksachen in der parlamentarischen Arbeit, wie zum Beispiel
    Anfragen, Anträgen und Beschlussvorlagen. Drucksachen werden in Form einer Beratung (oparl:Consultation) im
    Rahmen eines Tagesordnungspunkts (oparl:AgendaItem) einer Sitzung (oparl:Meeting) behandelt.

    Drucksachen spielen in der schriftlichen wie mündlichen Kommunikation eine besondere Rolle, da in vielen Texten auf
    bestimmte Drucksachen Bezug genommen wird. Hierbei kommen in parlamentarischen Informationssystemen in der Regel
    unveränderliche Kennungen der Drucksachen zum Einsatz.

    see https://oparl.org/spezifikation/online-ansicht/#entity-paper

        Attributes:
            id (UUID):
            id_ref (str):
            reference (str):
            date (datetime.date):
            type_ (Union[Unset, str]):  Default: 'https://schema.oparl.org/1.1/Paper'.
            body (Union[None, Unset, str]):
            name (Union[None, Unset, str]):
            paper_type (Union[None, Unset, str]):
            related_paper (Union[None, Unset, list['Paper']]):
            superordinated_paper (Union[None, Unset, list['Paper']]):
            subordinated_paper (Union[None, Unset, list['Paper']]):
            main_file (Union['OParlFile', None, Unset]):
            auxilary_file (Union[None, Unset, list['OParlFile']]):
            location (Union[None, Unset, list['OParlLocation']]):
            originator_person (Union[None, Unset, list['Person']]):
            under_direction_of (Union[None, Unset, list['Organization']]):
            originator_organization (Union[None, Unset, list['Organization']]):
            consultation (Union[None, Unset, list[str]]):
            license_ (Union[None, Unset, str]):
            keyword (Union[None, Unset, list[str]]):
            web (Union[None, Unset, str]):
            body_ref (Union[None, Unset, str]):
            related_papers_ref (Union[None, Unset, list[str]]):
            superordinated_paper_ref (Union[None, Unset, str]):
            subordinated_paper_ref (Union[None, Unset, list[str]]):
            main_file_ref (Union[None, Unset, str]):
            main_file_access_url (Union[None, Unset, str]):
            main_file_filename (Union[None, Unset, str]):
            auxilary_files_ref (Union[None, Unset, list[str]]):
            location_ref (Union[None, Unset, list[str]]):
            originator_person_ref (Union[None, Unset, list[str]]):
            under_direction_of_person_ref (Union[None, Unset, list[str]]):
            originator_organization_ref (Union[None, Unset, list[str]]):
            consultation_ref (Union[None, Unset, list[str]]):
            markdown_content (Union[None, Unset, str]):
    """

    id: UUID
    id_ref: str
    reference: str
    date: datetime.date
    type_: Union[Unset, str] = "https://schema.oparl.org/1.1/Paper"
    body: Union[None, Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    paper_type: Union[None, Unset, str] = UNSET
    related_paper: Union[None, Unset, list["Paper"]] = UNSET
    superordinated_paper: Union[None, Unset, list["Paper"]] = UNSET
    subordinated_paper: Union[None, Unset, list["Paper"]] = UNSET
    main_file: Union["OParlFile", None, Unset] = UNSET
    auxilary_file: Union[None, Unset, list["OParlFile"]] = UNSET
    location: Union[None, Unset, list["OParlLocation"]] = UNSET
    originator_person: Union[None, Unset, list["Person"]] = UNSET
    under_direction_of: Union[None, Unset, list["Organization"]] = UNSET
    originator_organization: Union[None, Unset, list["Organization"]] = UNSET
    consultation: Union[None, Unset, list[str]] = UNSET
    license_: Union[None, Unset, str] = UNSET
    keyword: Union[None, Unset, list[str]] = UNSET
    web: Union[None, Unset, str] = UNSET
    body_ref: Union[None, Unset, str] = UNSET
    related_papers_ref: Union[None, Unset, list[str]] = UNSET
    superordinated_paper_ref: Union[None, Unset, str] = UNSET
    subordinated_paper_ref: Union[None, Unset, list[str]] = UNSET
    main_file_ref: Union[None, Unset, str] = UNSET
    main_file_access_url: Union[None, Unset, str] = UNSET
    main_file_filename: Union[None, Unset, str] = UNSET
    auxilary_files_ref: Union[None, Unset, list[str]] = UNSET
    location_ref: Union[None, Unset, list[str]] = UNSET
    originator_person_ref: Union[None, Unset, list[str]] = UNSET
    under_direction_of_person_ref: Union[None, Unset, list[str]] = UNSET
    originator_organization_ref: Union[None, Unset, list[str]] = UNSET
    consultation_ref: Union[None, Unset, list[str]] = UNSET
    markdown_content: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.o_parl_file import OParlFile

        id = str(self.id)

        id_ref = self.id_ref

        reference = self.reference

        date = self.date.isoformat()

        type_ = self.type_

        body: Union[None, Unset, str]
        if isinstance(self.body, Unset):
            body = UNSET
        else:
            body = self.body

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        paper_type: Union[None, Unset, str]
        if isinstance(self.paper_type, Unset):
            paper_type = UNSET
        else:
            paper_type = self.paper_type

        related_paper: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.related_paper, Unset):
            related_paper = UNSET
        elif isinstance(self.related_paper, list):
            related_paper = []
            for related_paper_type_0_item_data in self.related_paper:
                related_paper_type_0_item = related_paper_type_0_item_data.to_dict()
                related_paper.append(related_paper_type_0_item)

        else:
            related_paper = self.related_paper

        superordinated_paper: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.superordinated_paper, Unset):
            superordinated_paper = UNSET
        elif isinstance(self.superordinated_paper, list):
            superordinated_paper = []
            for superordinated_paper_type_0_item_data in self.superordinated_paper:
                superordinated_paper_type_0_item = superordinated_paper_type_0_item_data.to_dict()
                superordinated_paper.append(superordinated_paper_type_0_item)

        else:
            superordinated_paper = self.superordinated_paper

        subordinated_paper: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.subordinated_paper, Unset):
            subordinated_paper = UNSET
        elif isinstance(self.subordinated_paper, list):
            subordinated_paper = []
            for subordinated_paper_type_0_item_data in self.subordinated_paper:
                subordinated_paper_type_0_item = subordinated_paper_type_0_item_data.to_dict()
                subordinated_paper.append(subordinated_paper_type_0_item)

        else:
            subordinated_paper = self.subordinated_paper

        main_file: Union[None, Unset, dict[str, Any]]
        if isinstance(self.main_file, Unset):
            main_file = UNSET
        elif isinstance(self.main_file, OParlFile):
            main_file = self.main_file.to_dict()
        else:
            main_file = self.main_file

        auxilary_file: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.auxilary_file, Unset):
            auxilary_file = UNSET
        elif isinstance(self.auxilary_file, list):
            auxilary_file = []
            for auxilary_file_type_0_item_data in self.auxilary_file:
                auxilary_file_type_0_item = auxilary_file_type_0_item_data.to_dict()
                auxilary_file.append(auxilary_file_type_0_item)

        else:
            auxilary_file = self.auxilary_file

        location: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, list):
            location = []
            for location_type_0_item_data in self.location:
                location_type_0_item = location_type_0_item_data.to_dict()
                location.append(location_type_0_item)

        else:
            location = self.location

        originator_person: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.originator_person, Unset):
            originator_person = UNSET
        elif isinstance(self.originator_person, list):
            originator_person = []
            for originator_person_type_0_item_data in self.originator_person:
                originator_person_type_0_item = originator_person_type_0_item_data.to_dict()
                originator_person.append(originator_person_type_0_item)

        else:
            originator_person = self.originator_person

        under_direction_of: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.under_direction_of, Unset):
            under_direction_of = UNSET
        elif isinstance(self.under_direction_of, list):
            under_direction_of = []
            for under_direction_of_type_0_item_data in self.under_direction_of:
                under_direction_of_type_0_item = under_direction_of_type_0_item_data.to_dict()
                under_direction_of.append(under_direction_of_type_0_item)

        else:
            under_direction_of = self.under_direction_of

        originator_organization: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.originator_organization, Unset):
            originator_organization = UNSET
        elif isinstance(self.originator_organization, list):
            originator_organization = []
            for originator_organization_type_0_item_data in self.originator_organization:
                originator_organization_type_0_item = originator_organization_type_0_item_data.to_dict()
                originator_organization.append(originator_organization_type_0_item)

        else:
            originator_organization = self.originator_organization

        consultation: Union[None, Unset, list[str]]
        if isinstance(self.consultation, Unset):
            consultation = UNSET
        elif isinstance(self.consultation, list):
            consultation = self.consultation

        else:
            consultation = self.consultation

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

        body_ref: Union[None, Unset, str]
        if isinstance(self.body_ref, Unset):
            body_ref = UNSET
        else:
            body_ref = self.body_ref

        related_papers_ref: Union[None, Unset, list[str]]
        if isinstance(self.related_papers_ref, Unset):
            related_papers_ref = UNSET
        elif isinstance(self.related_papers_ref, list):
            related_papers_ref = self.related_papers_ref

        else:
            related_papers_ref = self.related_papers_ref

        superordinated_paper_ref: Union[None, Unset, str]
        if isinstance(self.superordinated_paper_ref, Unset):
            superordinated_paper_ref = UNSET
        else:
            superordinated_paper_ref = self.superordinated_paper_ref

        subordinated_paper_ref: Union[None, Unset, list[str]]
        if isinstance(self.subordinated_paper_ref, Unset):
            subordinated_paper_ref = UNSET
        elif isinstance(self.subordinated_paper_ref, list):
            subordinated_paper_ref = self.subordinated_paper_ref

        else:
            subordinated_paper_ref = self.subordinated_paper_ref

        main_file_ref: Union[None, Unset, str]
        if isinstance(self.main_file_ref, Unset):
            main_file_ref = UNSET
        else:
            main_file_ref = self.main_file_ref

        main_file_access_url: Union[None, Unset, str]
        if isinstance(self.main_file_access_url, Unset):
            main_file_access_url = UNSET
        else:
            main_file_access_url = self.main_file_access_url

        main_file_filename: Union[None, Unset, str]
        if isinstance(self.main_file_filename, Unset):
            main_file_filename = UNSET
        else:
            main_file_filename = self.main_file_filename

        auxilary_files_ref: Union[None, Unset, list[str]]
        if isinstance(self.auxilary_files_ref, Unset):
            auxilary_files_ref = UNSET
        elif isinstance(self.auxilary_files_ref, list):
            auxilary_files_ref = self.auxilary_files_ref

        else:
            auxilary_files_ref = self.auxilary_files_ref

        location_ref: Union[None, Unset, list[str]]
        if isinstance(self.location_ref, Unset):
            location_ref = UNSET
        elif isinstance(self.location_ref, list):
            location_ref = self.location_ref

        else:
            location_ref = self.location_ref

        originator_person_ref: Union[None, Unset, list[str]]
        if isinstance(self.originator_person_ref, Unset):
            originator_person_ref = UNSET
        elif isinstance(self.originator_person_ref, list):
            originator_person_ref = self.originator_person_ref

        else:
            originator_person_ref = self.originator_person_ref

        under_direction_of_person_ref: Union[None, Unset, list[str]]
        if isinstance(self.under_direction_of_person_ref, Unset):
            under_direction_of_person_ref = UNSET
        elif isinstance(self.under_direction_of_person_ref, list):
            under_direction_of_person_ref = self.under_direction_of_person_ref

        else:
            under_direction_of_person_ref = self.under_direction_of_person_ref

        originator_organization_ref: Union[None, Unset, list[str]]
        if isinstance(self.originator_organization_ref, Unset):
            originator_organization_ref = UNSET
        elif isinstance(self.originator_organization_ref, list):
            originator_organization_ref = self.originator_organization_ref

        else:
            originator_organization_ref = self.originator_organization_ref

        consultation_ref: Union[None, Unset, list[str]]
        if isinstance(self.consultation_ref, Unset):
            consultation_ref = UNSET
        elif isinstance(self.consultation_ref, list):
            consultation_ref = self.consultation_ref

        else:
            consultation_ref = self.consultation_ref

        markdown_content: Union[None, Unset, str]
        if isinstance(self.markdown_content, Unset):
            markdown_content = UNSET
        else:
            markdown_content = self.markdown_content

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "id_ref": id_ref,
                "reference": reference,
                "date": date,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if body is not UNSET:
            field_dict["body"] = body
        if name is not UNSET:
            field_dict["name"] = name
        if paper_type is not UNSET:
            field_dict["paperType"] = paper_type
        if related_paper is not UNSET:
            field_dict["relatedPaper"] = related_paper
        if superordinated_paper is not UNSET:
            field_dict["superordinatedPaper"] = superordinated_paper
        if subordinated_paper is not UNSET:
            field_dict["subordinatedPaper"] = subordinated_paper
        if main_file is not UNSET:
            field_dict["mainFile"] = main_file
        if auxilary_file is not UNSET:
            field_dict["auxilaryFile"] = auxilary_file
        if location is not UNSET:
            field_dict["location"] = location
        if originator_person is not UNSET:
            field_dict["originatorPerson"] = originator_person
        if under_direction_of is not UNSET:
            field_dict["underDirectionOf"] = under_direction_of
        if originator_organization is not UNSET:
            field_dict["originatorOrganization"] = originator_organization
        if consultation is not UNSET:
            field_dict["consultation"] = consultation
        if license_ is not UNSET:
            field_dict["license"] = license_
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if web is not UNSET:
            field_dict["web"] = web
        if body_ref is not UNSET:
            field_dict["body_ref"] = body_ref
        if related_papers_ref is not UNSET:
            field_dict["relatedPapers_ref"] = related_papers_ref
        if superordinated_paper_ref is not UNSET:
            field_dict["superordinatedPaper_ref"] = superordinated_paper_ref
        if subordinated_paper_ref is not UNSET:
            field_dict["subordinatedPaper_ref"] = subordinated_paper_ref
        if main_file_ref is not UNSET:
            field_dict["mainFile_ref"] = main_file_ref
        if main_file_access_url is not UNSET:
            field_dict["mainFileAccessUrl"] = main_file_access_url
        if main_file_filename is not UNSET:
            field_dict["mainFileFilename"] = main_file_filename
        if auxilary_files_ref is not UNSET:
            field_dict["auxilaryFiles_ref"] = auxilary_files_ref
        if location_ref is not UNSET:
            field_dict["location_ref"] = location_ref
        if originator_person_ref is not UNSET:
            field_dict["originatorPerson_ref"] = originator_person_ref
        if under_direction_of_person_ref is not UNSET:
            field_dict["underDirectionOfPerson_ref"] = under_direction_of_person_ref
        if originator_organization_ref is not UNSET:
            field_dict["originatorOrganization_ref"] = originator_organization_ref
        if consultation_ref is not UNSET:
            field_dict["consultation_ref"] = consultation_ref
        if markdown_content is not UNSET:
            field_dict["markdown_content"] = markdown_content

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.o_parl_file import OParlFile
        from ..models.o_parl_location import OParlLocation
        from ..models.organization import Organization
        from ..models.person import Person

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        id_ref = d.pop("id_ref")

        reference = d.pop("reference")

        date = isoparse(d.pop("date")).date()

        type_ = d.pop("type", UNSET)

        def _parse_body(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        body = _parse_body(d.pop("body", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_paper_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        paper_type = _parse_paper_type(d.pop("paperType", UNSET))

        def _parse_related_paper(data: object) -> Union[None, Unset, list["Paper"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                related_paper_type_0 = []
                _related_paper_type_0 = data
                for related_paper_type_0_item_data in _related_paper_type_0:
                    related_paper_type_0_item = Paper.from_dict(related_paper_type_0_item_data)

                    related_paper_type_0.append(related_paper_type_0_item)

                return related_paper_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Paper"]], data)

        related_paper = _parse_related_paper(d.pop("relatedPaper", UNSET))

        def _parse_superordinated_paper(data: object) -> Union[None, Unset, list["Paper"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                superordinated_paper_type_0 = []
                _superordinated_paper_type_0 = data
                for superordinated_paper_type_0_item_data in _superordinated_paper_type_0:
                    superordinated_paper_type_0_item = Paper.from_dict(superordinated_paper_type_0_item_data)

                    superordinated_paper_type_0.append(superordinated_paper_type_0_item)

                return superordinated_paper_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Paper"]], data)

        superordinated_paper = _parse_superordinated_paper(d.pop("superordinatedPaper", UNSET))

        def _parse_subordinated_paper(data: object) -> Union[None, Unset, list["Paper"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                subordinated_paper_type_0 = []
                _subordinated_paper_type_0 = data
                for subordinated_paper_type_0_item_data in _subordinated_paper_type_0:
                    subordinated_paper_type_0_item = Paper.from_dict(subordinated_paper_type_0_item_data)

                    subordinated_paper_type_0.append(subordinated_paper_type_0_item)

                return subordinated_paper_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Paper"]], data)

        subordinated_paper = _parse_subordinated_paper(d.pop("subordinatedPaper", UNSET))

        def _parse_main_file(data: object) -> Union["OParlFile", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                main_file_type_0 = OParlFile.from_dict(data)

                return main_file_type_0
            except:  # noqa: E722
                pass
            return cast(Union["OParlFile", None, Unset], data)

        main_file = _parse_main_file(d.pop("mainFile", UNSET))

        def _parse_auxilary_file(data: object) -> Union[None, Unset, list["OParlFile"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                auxilary_file_type_0 = []
                _auxilary_file_type_0 = data
                for auxilary_file_type_0_item_data in _auxilary_file_type_0:
                    auxilary_file_type_0_item = OParlFile.from_dict(auxilary_file_type_0_item_data)

                    auxilary_file_type_0.append(auxilary_file_type_0_item)

                return auxilary_file_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["OParlFile"]], data)

        auxilary_file = _parse_auxilary_file(d.pop("auxilaryFile", UNSET))

        def _parse_location(data: object) -> Union[None, Unset, list["OParlLocation"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                location_type_0 = []
                _location_type_0 = data
                for location_type_0_item_data in _location_type_0:
                    location_type_0_item = OParlLocation.from_dict(location_type_0_item_data)

                    location_type_0.append(location_type_0_item)

                return location_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["OParlLocation"]], data)

        location = _parse_location(d.pop("location", UNSET))

        def _parse_originator_person(data: object) -> Union[None, Unset, list["Person"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                originator_person_type_0 = []
                _originator_person_type_0 = data
                for originator_person_type_0_item_data in _originator_person_type_0:
                    originator_person_type_0_item = Person.from_dict(originator_person_type_0_item_data)

                    originator_person_type_0.append(originator_person_type_0_item)

                return originator_person_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Person"]], data)

        originator_person = _parse_originator_person(d.pop("originatorPerson", UNSET))

        def _parse_under_direction_of(data: object) -> Union[None, Unset, list["Organization"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                under_direction_of_type_0 = []
                _under_direction_of_type_0 = data
                for under_direction_of_type_0_item_data in _under_direction_of_type_0:
                    under_direction_of_type_0_item = Organization.from_dict(under_direction_of_type_0_item_data)

                    under_direction_of_type_0.append(under_direction_of_type_0_item)

                return under_direction_of_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Organization"]], data)

        under_direction_of = _parse_under_direction_of(d.pop("underDirectionOf", UNSET))

        def _parse_originator_organization(data: object) -> Union[None, Unset, list["Organization"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                originator_organization_type_0 = []
                _originator_organization_type_0 = data
                for originator_organization_type_0_item_data in _originator_organization_type_0:
                    originator_organization_type_0_item = Organization.from_dict(
                        originator_organization_type_0_item_data
                    )

                    originator_organization_type_0.append(originator_organization_type_0_item)

                return originator_organization_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["Organization"]], data)

        originator_organization = _parse_originator_organization(d.pop("originatorOrganization", UNSET))

        def _parse_consultation(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                consultation_type_0 = cast(list[str], data)

                return consultation_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        consultation = _parse_consultation(d.pop("consultation", UNSET))

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

        def _parse_body_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        body_ref = _parse_body_ref(d.pop("body_ref", UNSET))

        def _parse_related_papers_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                related_papers_ref_type_0 = cast(list[str], data)

                return related_papers_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        related_papers_ref = _parse_related_papers_ref(d.pop("relatedPapers_ref", UNSET))

        def _parse_superordinated_paper_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        superordinated_paper_ref = _parse_superordinated_paper_ref(d.pop("superordinatedPaper_ref", UNSET))

        def _parse_subordinated_paper_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                subordinated_paper_ref_type_0 = cast(list[str], data)

                return subordinated_paper_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        subordinated_paper_ref = _parse_subordinated_paper_ref(d.pop("subordinatedPaper_ref", UNSET))

        def _parse_main_file_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        main_file_ref = _parse_main_file_ref(d.pop("mainFile_ref", UNSET))

        def _parse_main_file_access_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        main_file_access_url = _parse_main_file_access_url(d.pop("mainFileAccessUrl", UNSET))

        def _parse_main_file_filename(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        main_file_filename = _parse_main_file_filename(d.pop("mainFileFilename", UNSET))

        def _parse_auxilary_files_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                auxilary_files_ref_type_0 = cast(list[str], data)

                return auxilary_files_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        auxilary_files_ref = _parse_auxilary_files_ref(d.pop("auxilaryFiles_ref", UNSET))

        def _parse_location_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                location_ref_type_0 = cast(list[str], data)

                return location_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        location_ref = _parse_location_ref(d.pop("location_ref", UNSET))

        def _parse_originator_person_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                originator_person_ref_type_0 = cast(list[str], data)

                return originator_person_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        originator_person_ref = _parse_originator_person_ref(d.pop("originatorPerson_ref", UNSET))

        def _parse_under_direction_of_person_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                under_direction_of_person_ref_type_0 = cast(list[str], data)

                return under_direction_of_person_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        under_direction_of_person_ref = _parse_under_direction_of_person_ref(d.pop("underDirectionOfPerson_ref", UNSET))

        def _parse_originator_organization_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                originator_organization_ref_type_0 = cast(list[str], data)

                return originator_organization_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        originator_organization_ref = _parse_originator_organization_ref(d.pop("originatorOrganization_ref", UNSET))

        def _parse_consultation_ref(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                consultation_ref_type_0 = cast(list[str], data)

                return consultation_ref_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        consultation_ref = _parse_consultation_ref(d.pop("consultation_ref", UNSET))

        def _parse_markdown_content(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        markdown_content = _parse_markdown_content(d.pop("markdown_content", UNSET))

        paper = cls(
            id=id,
            id_ref=id_ref,
            reference=reference,
            date=date,
            type_=type_,
            body=body,
            name=name,
            paper_type=paper_type,
            related_paper=related_paper,
            superordinated_paper=superordinated_paper,
            subordinated_paper=subordinated_paper,
            main_file=main_file,
            auxilary_file=auxilary_file,
            location=location,
            originator_person=originator_person,
            under_direction_of=under_direction_of,
            originator_organization=originator_organization,
            consultation=consultation,
            license_=license_,
            keyword=keyword,
            web=web,
            body_ref=body_ref,
            related_papers_ref=related_papers_ref,
            superordinated_paper_ref=superordinated_paper_ref,
            subordinated_paper_ref=subordinated_paper_ref,
            main_file_ref=main_file_ref,
            main_file_access_url=main_file_access_url,
            main_file_filename=main_file_filename,
            auxilary_files_ref=auxilary_files_ref,
            location_ref=location_ref,
            originator_person_ref=originator_person_ref,
            under_direction_of_person_ref=under_direction_of_person_ref,
            originator_organization_ref=originator_organization_ref,
            consultation_ref=consultation_ref,
            markdown_content=markdown_content,
        )

        paper.additional_properties = d
        return paper

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
