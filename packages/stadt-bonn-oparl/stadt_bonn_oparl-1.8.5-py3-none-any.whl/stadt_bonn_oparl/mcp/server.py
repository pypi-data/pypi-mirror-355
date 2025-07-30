import http
from re import I
from typing import Any, List, Optional
import uuid

import httpx
import logfire
from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings

from stadt_bonn_oparl import __version__ as stadt_bonn_oparl_version
from stadt_bonn_oparl.api.helpers.consultations import _get_consultation
from stadt_bonn_oparl.api.helpers.helpers import _get_paper_by_id
from stadt_bonn_oparl.api.helpers.meetings import _get_meeting
from stadt_bonn_oparl.api.models import Consultation, MeetingResponse, PaperResponse
from stadt_bonn_oparl.config import OPARL_BASE_URL, UPSTREAM_API_URL
from stadt_bonn_oparl.logging import configure_logging
from stadt_bonn_oparl.oparl_fetcher import get_oparl_data, get_oparl_list_data
from stadt_bonn_oparl.utils import extract_id_from_oparl_url
from stadt_bonn_oparl.research import ResearchService, ComprehensiveResearchResult

mcp = FastMCP("oparl, Stadt Bonn")

# Initialize research service
research_service = ResearchService()

configure_logging(1)

logfire.configure(
    service_name="stadt-bonn-oparl-mcp",
    service_version=stadt_bonn_oparl_version,
)
logfire.instrument_pydantic()
logfire.instrument_mcp()


@mcp.resource(
    "data://version",
    name="Version",
    description="Version information for the OParl MCP",
    mime_type="application/json",
)
def get_version() -> dict:
    return {"version": stadt_bonn_oparl_version, "name": "stadt-bonn-oparl-mcp"}


@mcp.resource(
    "oparl://system",
    name="OPARL System der Stadt Bonn, see https://oparl.org/spezifikation/online-ansicht/#entity-system",
    description="Ein oparl:System-Objekt repräsentiert eine OParl-Schnittstelle für eine bestimmte OParl-Version. Es ist außerdem der Startpunkt für Clients beim Zugriff auf einen Server. Die ist das Sysem-Object der Stadt Bonn",
    mime_type="application/json",
)
async def get_system() -> Optional[dict[str, Any]]:
    """Get the system information from the OParl API"""
    return await get_oparl_data("/system")


@mcp.tool()
async def stadt_bonn_oparl_summarize_meeting(meeting_id: int) -> str:
    """
    📅 Erstellt eine Zusammenfassung eines OParl Meetings der Stadt Bonn.

    Diese Funktion ruft Meeting-Daten ab (zuerst aus ChromaDB, dann aus API) und
    erstellt eine strukturierte Zusammenfassung mit allen wichtigen Informationen.

    Args:
        meeting_id: Die ID des Meetings

    Returns:
        Eine formatierte Zusammenfassung des Meetings
    """
    # Initialize clients
    http_client = httpx.Client(base_url=OPARL_BASE_URL)
    chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        collection = chromadb_client.get_collection(name="meetings")

        # Try to get from ChromaDB first
        meeting_id_ref = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL, f"{UPSTREAM_API_URL}/meetings?id={meeting_id}"
            )
        )
        results = collection.get(ids=[meeting_id_ref])

        if results and results["documents"]:
            meeting = MeetingResponse.model_validate_json(results["documents"][0])
        else:
            # Fallback to API
            meeting = await _get_meeting(
                meeting_id=meeting_id,
                http_client=http_client,
            )

        if not meeting:
            return f"❌ Meeting mit ID {meeting_id} nicht gefunden."

        # Build summary
        summary_parts = [
            f"# 📅 Meeting-Zusammenfassung: {meeting.name}",
            f"\n**ID:** {meeting.id}",
            f"**Datum:** {meeting.start} Uhr",
        ]

        if meeting.location_ref:
            summary_parts.append(
                f"**Ort:** {meeting.location_ref if hasattr(meeting.location_ref, 'name') else 'Details verfügbar'}"
            )

        if meeting.organizations_ref:
            summary_parts.append(
                f"**Organisation:** {meeting.organizations_ref[0] if meeting.organizations_ref else 'N/A'}"
            )

        # Meeting status
        if meeting.cancelled:
            summary_parts.append("\n⚠️ **Status:** ABGESAGT")

        # Participant count
        if meeting.participant_ref:
            summary_parts.append(f"\n👥 **Teilnehmer:** {len(meeting.participant_ref)}")

        # Files
        file_info = []
        if meeting.invitation:
            file_info.append("📄 Einladung")
        if meeting.verbatimProtocol:
            file_info.append("📝 Wortprotokoll")
        if meeting.auxiliaryFile:
            file_info.append(f"📎 {len(meeting.auxiliaryFile)} weitere Dateien")
        if file_info:
            summary_parts.append(f"\n**Dokumente:** {', '.join(file_info)}")

        # Agenda items
        if meeting.agendaItem:
            summary_parts.append(
                f"\n## 📋 Tagesordnung ({len(meeting.agendaItem)} Punkte)\n"
            )

            for i, item in enumerate(meeting.agendaItem[:5], 1):  # Show first 5 items
                summary_parts.append(f"**{item.number or i}.** {item.name}")
                if item.consultation and len(item.consultation) > 0:
                    summary_parts.append(f"   ↳ {len(item.consultation)} Beratung(en)")

            if len(meeting.agendaItem) > 5:
                summary_parts.append(
                    f"\n... und {len(meeting.agendaItem) - 5} weitere Tagesordnungspunkte"
                )

        # Keywords if available
        if hasattr(meeting, "keyword") and meeting.keyword:
            summary_parts.append(f"\n**Schlagworte:** {', '.join(meeting.keyword)}")

        return "\n".join(summary_parts)

    except Exception as e:
        return f"❌ Fehler beim Abrufen des Meetings {meeting_id}: {str(e)}"
    finally:
        http_client.close()


@mcp.prompt()
def meeting_summary_prompt(meeting_id: int) -> str:
    """
    🎯 Prompt für die Zusammenfassung eines OParl Meetings der Stadt Bonn.

    Dieser Prompt hilft bei der strukturierten Analyse und Zusammenfassung
    von Sitzungen des Bonner Stadtrats und seiner Gremien.

    Args:
        meeting_id: Die ID des zu analysierenden Meetings

    Returns:
        Ein strukturierter Prompt für die Meeting-Analyse
    """
    return f"""Du bist ein Assistent für die Analyse von Sitzungen der Stadt Bonn.

Bitte analysiere das Meeting mit der ID {meeting_id} und erstelle eine strukturierte Zusammenfassung.

Nutze dazu das Tool `stadt_bonn_oparl_summarize_meeting` mit der Meeting-ID {meeting_id}.

Nach dem Abruf der Daten, strukturiere die Informationen wie folgt:

1. **Grundinformationen**: Datum, Ort, Gremium
2. **Wichtige Tagesordnungspunkte**: Die relevantesten Themen
3. **Beratungen**: Welche Vorlagen wurden besprochen
4. **Teilnehmende**: Anzahl und ggf. wichtige Personen
5. **Dokumente**: Verfügbare Unterlagen

Wenn das Meeting abgesagt wurde, hebe dies deutlich hervor.

Ziel ist eine kompakte, aber informative Übersicht für Bürger:innen."""


@mcp.tool()
async def stadt_bonn_oparl_paper_summary(paper_id: str) -> Optional[dict[str, Any]]:
    """
    📄 Generates a summary for a specific Drucksache/Paper in the OParl API.

    It does not deliver all data, but a summary of the paper including
    consultations, related meetings and important metadata.

    Args:
        paper_id: The ID of the paper to summarize

    Returns:
        A dictionary containing the paper summary or None if not found
    """
    paper_data = await get_paper(paper_id)
    if paper_data:
        # Generate a summary based on the paper data
        summary = {
            "title": paper_data.get("name"),
            "id": paper_data.get("id"),
            "reference": paper_data.get("reference"),
            "date": paper_data.get("date"),
            "paperType": paper_data.get("paperType"),
            "consultations": [],
        }

        # Add consultation data if available
        if "consultation" in paper_data:
            consultations = paper_data["consultation"]
            if isinstance(consultations, list):
                for consultation_url in consultations[:5]:  # Limit to first 5
                    consultation_id = extract_id_from_oparl_url(consultation_url)
                    if consultation_id:
                        consultation_data = await _get_consultation(consultation_id)
                        if consultation_data:
                            consultation_summary = {
                                "meeting": consultation_data.get("meeting"),
                                "agendaItem": consultation_data.get("agendaItem"),
                                "authoritative": consultation_data.get("authoritative"),
                            }
                            summary["consultations"].append(consultation_summary)

        # Add additional metadata
        summary["mainFile"] = paper_data.get("mainFile")
        summary["auxiliaryFile"] = paper_data.get("auxiliaryFile")
        summary["originatorOrganization"] = paper_data.get("originatorOrganization")
        summary["underDirectionOf"] = paper_data.get("underDirectionOf")
        summary["keyword"] = paper_data.get("keyword", [])

        return summary
    return None


@mcp.tool()
async def stadt_bonn_oparl_organization_summary(
    organization_id: str,
) -> Optional[dict[str, Any]]:
    """
    🏛️ Generates a summary for a specific Organisation in the OParl API.

    It does not deliver all data, but a summary of the organization including
    members, meetings and key information.

    Args:
        organization_id: The ID of the organization to summarize

    Returns:
        A dictionary containing the organization summary or None if not found
    """
    organization_data = await get_organization(organization_id)
    if organization_data:
        summary = {
            "title": organization_data.get("name"),
            "id": organization_data.get("id"),
            "organizationType": organization_data.get("organizationType"),
            "classification": organization_data.get("classification"),
            "startDate": organization_data.get("startDate"),
            "endDate": organization_data.get("endDate"),
        }

        # Add member count if available
        if "membership" in organization_data:
            memberships = organization_data.get("membership", [])
            summary["memberCount"] = len(memberships)

        # Add meeting information if available
        if "meeting" in organization_data:
            meetings = organization_data.get("meeting", [])
            summary["meetingCount"] = len(meetings)
            summary["recentMeetings"] = meetings[:5]  # Last 5 meetings

        # Add additional metadata
        summary["location"] = organization_data.get("location")
        summary["website"] = organization_data.get("website")

        return summary
    return None


@mcp.tool()
async def stadt_bonn_oparl_person_search(
    query: str,
) -> Optional[List[dict[str, Any]]]:
    """
    👤 Search for persons in the OParl API based on a query string.

    Searches for city council members, committee members and other persons
    in the Bonn political system.

    Args:
        query: The search query string (name or part of name)

    Returns:
        A list of person summaries matching the query or None if no results
    """
    async with httpx.AsyncClient() as client:
        # Fetch the person data from the OParl API
        response = await client.get(
            f"{OPARL_BASE_URL}/search/", params={"query": query}
        )
        if response.status_code == 200:
            search_results = response.json()
            persons = []
            for result in search_results.get("data", []):
                if result.get("type") == "https://schema.oparl.org/1.1/Person":
                    person_summary = {
                        "id": extract_id_from_oparl_url(result.get("id")),
                        "name": result.get("name"),
                        "familyName": result.get("familyName"),
                        "givenName": result.get("givenName"),
                        "title": result.get("title"),
                    }
                    persons.append(person_summary)
            return persons if persons else None
    return None


@mcp.tool()
async def research_topic_comprehensive(topic: str) -> ComprehensiveResearchResult:
    """
    🔍 Umfassende Themenrecherche zu einem kommunalpolitischen Thema.

    Diese Funktion durchsucht alle relevanten Dokumente, Sitzungen und Entscheidungen
    zu einem bestimmten Thema in der Bonner Kommunalpolitik.

    Args:
        topic: Das zu recherchierende Thema (z.B. "Radverkehr", "Klimaschutz")

    Returns:
        Eine umfassende Analyse mit allen relevanten Informationen zum Thema
    """
    return await research_service.research_topic_comprehensive(topic)


@mcp.prompt()
def get_paper_summary() -> str:
    """
    Prompt template for analyzing OParl papers from Stadt Bonn.
    """
    return """schau dir die das paper mit der id 2022736 im allris der stadt bonn an, und gibt mir einen kleinen überblick. gehe vor allem auf die sitzungen ein in denen die durcksache bearbeitet worden ist, und welche personen wichtig sind. nutze deutsche sprache für deine antwort. schreib einen flashy and glossy eilmeldung im stil von spiegel online, ueberpruefe fuer jeden link ob er wirklich erreichbar ist, zB mit `curl`"""


# Resources that already exist
@mcp.resource(
    "oparl://body/{body_id}",
    name="OPARL Body, Allris der Stadt Bonn",
    description="Eine Körperschaft ist diejenige Organisationsebene, auf der die Körperschaft müssen in der bundesrepublikanischen Struktur in Deutschland eingeordnet werden: Kreise, Städte, Gemeinden, Bezirke und Stadtteile.",
    mime_type="application/json",
)
async def get_body(body_id: str) -> Optional[dict[str, Any]]:
    """Get the body information from the OParl API"""
    return await get_oparl_data("/bodies", params={"id": body_id})


@mcp.resource(
    "oparl://paper/{paper_id}/content",
    name="OPARL Paper Content, Allris der Stadt Bonn",
    description="Dieser Objekttyp dient der Abbildung von Inhalten von Drucksachen in der parlamentarischen Arbeit, wie zum Beispiel Anfragen, Anträgen und Beschlussvorlagen.",
    mime_type="application/json",
)
async def get_paper_content(paper_id: str) -> Optional[dict[str, Any]]:
    """Get the paper content from the OParl API"""
    return await get_oparl_data("/papers", params={"id": paper_id})


@mcp.resource(
    "oparl://paper/{paper_id}",
    name="OPARL Paper, Allris der Stadt Bonn",
    description="Dieser Objekttyp dient der Abbildung von Drucksachen in der parlamentarischen Arbeit, wie zum Beispiel Anfragen, Anträgen und Beschlussvorlagen. Drucksachen werden in Form einer Beratung (oparl:Consultation) im Rahmen eines Tagesordnungspunkts (oparl:AgendaItem) einer Sitzung (oparl:Meeting) behandelt.",
    mime_type="application/json",
)
async def get_paper(paper_id: int) -> Optional[PaperResponse]:
    """Get the paper information from the OParl API"""
    http_client = httpx.Client(base_url=OPARL_BASE_URL)
    chromadb_client = chromadb.PersistentClient(
        path="./chroma-api",
        settings=Settings(anonymized_telemetry=False),
    )
    collection = chromadb_client.get_collection(name="papers")
    return await _get_paper_by_id(http_client, collection, paper_id)


@mcp.resource(
    "oparl://papers/last_20",
    name="OPARL last 20 Papers, Allris der Stadt Bonn",
    description="Die letzen/aktuellsten 20 Drucksachen, der Objekttyp Drucksache dient der Abbildung von Drucksachen in der parlamentarischen Arbeit, wie zum Beispiel Anfragen, Anträgen und Beschlussvorlagen. Drucksachen werden in Form einer Beratung (oparl:Consultation) im Rahmen eines Tagesordnungspunkts (oparl:AgendaItem) einer Sitzung (oparl:Meeting) behandelt.",
    mime_type="application/json",
)
async def get_last_20_papers() -> Optional[List[str]]:
    """Get the IDs of the last 20 papers from the OParl API"""
    papers_data = await get_oparl_list_data("/papers")

    if papers_data:
        paper_ids: List[str] = []
        for paper_item in papers_data:
            if isinstance(paper_item, dict) and "id" in paper_item:
                extracted_id = extract_id_from_oparl_url(paper_item["id"])
                if extracted_id:
                    paper_ids.append(extracted_id)
        return paper_ids
    return None


@mcp.resource(
    "oparl://person/{person_id}",
    name="OPARL Person, Allris der Stadt Bonn",
    description="Dieser Objekttyp dient der Abbildung von Personen in der parlamentarischen Arbeit, wie zum Beispiel Ratsmitgliedern, Bürgern und Mitarbeitern.",
    mime_type="application/json",
)
async def get_person(person_id: str) -> Optional[dict[str, Any]]:
    """Get the person information from the OParl API"""
    return await get_oparl_data("/persons", params={"id": person_id})


@mcp.resource(
    "oparl://consultation/{consultation_id}",
    name="OPARL Consultation, Allris der Stadt Bonn",
    description="Der Objekttyp oparl:Consultation dient dazu, die Beratung einer Drucksache (oparl:Paper) in einer Sitzung abzubilden. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit stattgefunden hat oder diese für die Zukunft geplant ist. Die Gesamtheit aller Objekte des Typs oparl:Consultation zu einer bestimmten Drucksache bildet das ab, was in der Praxis als Beratungsfolge der Drucksache bezeichnet wird.",
    mime_type="application/json",
)
async def get_consultation(consultation_id: str) -> Optional[dict[str, Any]]:
    """Get the consultation information from the OParl API"""
    return await get_oparl_data("/consultations", params={"id": consultation_id})


@mcp.resource(
    "oparl://meeting/{meeting_id}",
    name="OPARL Meeting, Allris der Stadt Bonn",
    description="Eine Sitzung ist die Versammlung einer oder mehrerer Gruppierungen (oparl:Organization) zu einem bestimmten Zeitpunkt an einem bestimmten Ort. Die geladenen Teilnehmer der Sitzung sind jeweils als Objekte vom Typ oparl:Person, die in entsprechender Form referenziert werden. Verschiedene Dateien (Einladung, Ergebnis- und Wortprotokoll, sonstige Anlagen) können referenziert werden. Die Inhalte einer Sitzung werden durch Tagesordnungspunkte (oparl:AgendaItem) abgebildet.",
    mime_type="application/json",
)
async def get_meeting(meeting_id: str) -> Optional[dict[str, Any]]:
    """Get the meeting information from the OParl API"""
    return await get_oparl_data("/meetings", params={"id": meeting_id})


@mcp.resource(
    "oparl://agenda_item/{agenda_item_id}",
    name="OPARL Agenda Item, Allris der Stadt Bonn",
    description="Tagesordnungspunkte sind die Bestandteile von Sitzungen (oparl:Meeting). Jeder Tagesordnungspunkt widmet sich inhaltlich einem bestimmten Thema, wozu in der Regel auch die Beratung bestimmter Drucksachen gehört. Die Beziehung zwischen einem Tagesordnungspunkt und einer Drucksache wird über ein Objekt vom Typ oparl:Consultation hergestellt, das über die Eigenschaft consultation referenziert werden kann.",
    mime_type="application/json",
)
async def get_agenda_item(agenda_item_id: str) -> Optional[dict[str, Any]]:
    """Get the agenda item information from the OParl API"""
    return await get_oparl_data("/agendaItems", params={"id": agenda_item_id})


@mcp.resource(
    "oparl://organization/{organization_id}",
    name="OPARL Organization, Allris der Stadt Bonn",
    description="Dieser Objekttyp dient dazu, Gruppierungen von Personen abzubilden, die in der parlamentarischen Arbeit eine Rolle spielen. Dazu zählen in der Praxis insbesondere Fraktionen und Gremien.",
    mime_type="application/json",
)
async def get_organization(organization_id: str) -> Optional[dict[str, Any]]:
    """Get the organization information from the OParl API"""
    return await get_oparl_data("/organizations/", params={"id": organization_id})
