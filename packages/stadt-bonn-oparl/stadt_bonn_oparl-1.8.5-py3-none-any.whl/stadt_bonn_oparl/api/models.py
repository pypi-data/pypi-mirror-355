import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel

from stadt_bonn_oparl.models import (
    Meeting,
    Membership,
    OParlAgendaItem,
    OParlFile,
    OParlLocation,
    Organization,
    Paper,
    Person,
)


class OParlEntity(BaseModel):
    """Base model for OParl API responses."""

    created: Optional[datetime.datetime] = None
    modified: Optional[datetime.datetime] = None
    deleted: bool = False


class SystemResponse(OParlEntity):
    """Model for the system response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/System"
    oparlVersion: str = "https://schema.oparl.org/1.1/"
    otherOparlVersions: Optional[list[str]] = None
    license: Optional[str]
    body: str
    name: str
    contactEmail: Optional[str] = None
    contactName: Optional[str] = None
    website: Optional[str] = None
    vendor: str = "Mach! Den! Staat!"
    product: str = "Stadt Bonn OParl API Cache"


class PersonResponse(OParlEntity, Person):
    """Model for the person response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/Person"

    membership_ref: Optional[List[str]] = None
    location_ref: Optional[str] = None


class PersonListResponse(BaseModel):
    """Model for a list of persons from the OParl API."""

    data: List[PersonResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class MembershipResponse(OParlEntity, Membership):
    """Model for the membership response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/Membership"

    person_ref: Optional[str] = None  # Internal use only, not part of the OParl schema

    organization_ref: Optional[str] = (
        None  # Internal use only, not part of the OParl schema
    )


class MembershipListResponse(BaseModel):
    """Model for a list of memberships from the OParl API."""

    data: List[MembershipResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class LocationResponse(OParlEntity, OParlLocation):
    """Model for the location response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/Location"


class LocationListResponse(BaseModel):
    """Model for a list of locations from the OParl API."""

    data: List[LocationResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class OrganizationResponse(OParlEntity, Organization):
    """Model for the organization response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/Organization"

    membership_ref: Optional[List[str]] = (
        None  # Internal use only, not part of the OParl schema
    )
    location_ref: Optional[str] = (
        None  # Internal use only, not part of the OParl schema
    )
    meeting_ref: Optional[str] = None  # Internal use only, not part of the OParl schema


class OrganizationListResponse(BaseModel):
    """Model for a list of organizations from the OParl API."""

    data: List[OrganizationResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class MeetingResponse(OParlEntity, Meeting):
    """Model for the meeting response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/Meeting"

    location_ref: Optional[str] = (
        None  # Internal use only, not part of the OParl schema
    )
    organizations_ref: Optional[List[str]] = (
        None  # Internal use only, not part of the OParl schema
    )
    participant_ref: Optional[List[str]] = (
        None  # Internal use only, not part of the OParl schema
    )


class MeetingListResponse(BaseModel):
    """Model for a list of meetings from the OParl API."""

    data: List[MeetingResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class AgendaItemResponse(OParlEntity, OParlAgendaItem):
    """Model for the agenda item response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/AgendaItem"


class AgendaItemListResponse(BaseModel):
    """Model for a list of agenda items from the OParl API."""

    data: List[AgendaItemResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class FileResponse(OParlEntity, OParlFile):
    """Model for the file response from the OParl API."""

    type: str = "https://schema.oparl.org/1.1/File"

    agendaItem_ref: Optional[List[str]] = (
        None  # Internal use only, not part of the OParl schema
    )
    meeting_ref: Optional[str] = None  # Internal use only, not part of the OParl schema
    paper_ref: Optional[str] = None  # Internal use only, not part of the OParl schema


class FileListResponse(BaseModel):
    """Model for a list of files from the OParl API."""

    data: List[FileResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class PaperResponse(OParlEntity, Paper):
    """Model for the paper response from the OParl API."""


class PaperListResponse(BaseModel):
    """Model for a list of papers from the OParl API."""

    data: List[PaperResponse] = []

    pagination: Optional[dict] = None
    links: Optional[dict] = None


class Consultation(OParlEntity):
    """Der Objekttyp oparl:Consultation dient dazu, die Beratung einer Drucksache (oparl:Paper) in einer Sitzung
    abzubilden. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit stattgefunden hat oder diese
    für die Zukunft geplant ist. Die Gesamtheit aller Objekte des Typs oparl:Consultation zu einer bestimmten
    Drucksache bildet das ab, was in der Praxis als “Beratungsfolge” der Drucksache bezeichnet wird.
    """

    id: (
        uuid.UUID
    )  # Unique identifier for the organization, e.g. "123e4567-e89b-12d3-a456-426614174000"
    id_ref: (
        str  # this referes to the upstream ID, which is depends on the organizationType
    )

    bi: int = 0  # Bi-Nummer der Drucksache, falls vorhanden

    type: str = "https://schema.oparl.org/1.1/Consultation"

    authoritative: bool = (
        True  # Drückt aus, ob bei dieser Beratung ein Beschluss zu der Drucksache gefasst wird/wurde oder nicht.
    )
    role: Optional[
        str
    ]  # Rolle oder Funktion der Beratung. Zum Beispiel Anhörung, Entscheidung, Kenntnisnahme, Vorberatung usw.

    license: Optional[str] = None  # Lizenz für die Beratung, falls vorhanden
    keyword: Optional[List[str]] = None  # Schlagwörter, die die Beratung beschreiben

    web: Optional[str] = None  # URL zur Webseite der Beratung, falls vorhanden

    paper: Optional[Paper] = (
        None  # TODO: these should be fetched from the OParl API and injected here
    )
    meeting: Optional[Meeting] = (
        None  # TODO: these should be fetched from the OParl API and injected here
    )
    paper_ref: Optional[str] = None  # Internal use only, not part of the OParl schema
    meeting_ref: Optional[str] = None  # Internal use only, not part of the OParl schema
    organizations: List[Organization] = []
    organization_ref: Optional[List[str]] = (
        None  # Internal use only, not part of the OParl schema
    )
