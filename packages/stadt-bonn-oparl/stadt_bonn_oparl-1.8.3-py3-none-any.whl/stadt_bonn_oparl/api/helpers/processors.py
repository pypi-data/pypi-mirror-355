import uuid

from httpx import URL

from stadt_bonn_oparl.api.config import SELF_API_URL, UPSTREAM_API_URL


def _update_id(o: dict) -> None:
    """Helper function to update the ID of an object to a UUID and save the original ID as id_ref."""

    # FIXME: why do we do this? because oparl org id 354 typ-parameter depending WTF?!?!
    # Convert the ID to a UUID using the URL namespace

    if "id" in o and o["id"] is not None:
        # Convert the ID to a UUID using the URL namespace
        o["id_ref"] = str(URL(o["id"]))  # let's normalize the URL first
        o["id"] = uuid.uuid5(uuid.NAMESPACE_URL, o["id_ref"])


def _update_organization_attribute(d: dict) -> None:
    """Helper to convert the organization attribute (might be str or list of strings) to a list of references."""
    if "organization" in d and d["organization"]:
        if isinstance(d["organization"], list):
            d["organizations_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL) for url in d["organization"]
            ]
        elif isinstance(d["organization"], str):
            d["rganizations_ref"] = [
                d["organization"].replace(UPSTREAM_API_URL, SELF_API_URL)
            ]
        else:
            d["organizations_ref"] = None
    else:
        d["organizations_ref"] = None
    d["organization"] = None


def _process_organization(org: dict) -> None:
    """Helper function to process organization data by converting URLs."""
    _update_id(org)

    if "membership" in org and org["membership"] is not None:
        # rewrite each membership URL
        org["membership_ref"] = [
            membership.replace(UPSTREAM_API_URL, SELF_API_URL)
            for membership in org["membership"]
        ]
    else:
        org["membership_ref"] = None
    org["membership"] = None

    if "location" in org and org["location"] is not None:
        org["location_ref"] = org["location"]["id"].replace(
            UPSTREAM_API_URL, SELF_API_URL
        )
    else:
        org["location_ref"] = None
    org["location"] = None

    if "meeting" in org and org["meeting"] is not None:
        org["meeting_ref"] = org["meeting"].replace(UPSTREAM_API_URL, SELF_API_URL)
    else:
        org["meeting_ref"] = None
    org["meeting"] = None


def _process_paper(paper: dict) -> None:
    """Helper function to process paper data by converting URLs."""
    _update_id(paper)

    # Process reference fields to convert URLs from upstream to self API
    paper["body_ref"] = paper.get("body", None)
    if paper["body_ref"]:
        paper["body_ref"] = paper["body_ref"].replace(UPSTREAM_API_URL, SELF_API_URL)
    paper["body"] = None

    # Process relatedPapers
    if "relatedPaper" in paper and paper["relatedPaper"]:
        paper["relatedPapers_ref"] = [
            url.replace(UPSTREAM_API_URL, SELF_API_URL) for url in paper["relatedPaper"]
        ]
    else:
        paper["relatedPapers_ref"] = None
    paper["relatedPaper"] = None

    # Process superordinatedPaper
    paper["superordinatedPaper_ref"] = paper.get("superordinatedPaper", None)
    if paper["superordinatedPaper_ref"]:
        paper["superordinatedPaper_ref"] = paper["superordinatedPaper_ref"].replace(
            UPSTREAM_API_URL, SELF_API_URL
        )
    paper["superordinatedPaper"] = None

    # Process subordinatedPaper
    if "subordinatedPaper" in paper and paper["subordinatedPaper"]:
        paper["subordinatedPaper_ref"] = [
            url.replace(UPSTREAM_API_URL, SELF_API_URL)
            for url in paper["subordinatedPaper"]
        ]
    else:
        paper["subordinatedPaper_ref"] = None
    paper["subordinatedPaper"] = None

    # Process mainFile - could be an object with id field or a string
    if "mainFile" in paper and paper["mainFile"]:
        if isinstance(paper["mainFile"], dict) and "id" in paper["mainFile"]:
            paper["mainFile_ref"] = paper["mainFile"]["id"].replace(
                UPSTREAM_API_URL, SELF_API_URL
            )
            paper["mainFileAccessUrl"] = paper["mainFile"].get("accessUrl", None)
            paper["mainFileFilename"] = paper["mainFile"].get("fileName", None)
        elif isinstance(paper["mainFile"], str):
            paper["mainFile_ref"] = paper["mainFile"].replace(
                UPSTREAM_API_URL, SELF_API_URL
            )
        else:
            paper["mainFile_ref"] = None
    else:
        paper["mainFile_ref"] = None
    paper["mainFile"] = None

    # Process auxilaryFile
    if "auxilaryFile" in paper and paper["auxilaryFile"]:
        paper["auxilaryFiles_ref"] = [
            url.replace(UPSTREAM_API_URL, SELF_API_URL) for url in paper["auxilaryFile"]
        ]
    else:
        paper["auxilaryFiles_ref"] = None
    paper["auxilaryFile"] = None

    # Process location - convert list to list of refs
    if "location" in paper and paper["location"]:
        if isinstance(paper["location"], list):
            # FIXME: I think upstream is broken... location[] might have broken URLs
            # e.g. https://www.bonn.sitzung-online.de/public/locations?id=1234567 missing the 'oparl/' path
            fixed_locations = []
            for paper_location in paper["location"]:
                if not paper_location.startswith(UPSTREAM_API_URL):
                    paper_location = paper_location.replace(
                        "https://www.bonn.sitzung-online.de/public/locations?id=",
                        UPSTREAM_API_URL + "/locations?id=",
                    )
                fixed_locations.append(paper_location)
            paper["location_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL) for url in fixed_locations
            ]
        elif isinstance(paper["location"], str):
            fixed_location = paper["location"]
            if not paper["location"].startswith(UPSTREAM_API_URL):
                fixed_location = paper["location"].replace(
                    "https://www.bonn.sitzung-online.de/public/locations?id=",
                    UPSTREAM_API_URL + "/locations?id=",
                )
            paper["location_ref"] = [
                fixed_location.replace(UPSTREAM_API_URL, SELF_API_URL)
            ]
        else:
            paper["location_ref"] = None
    else:
        paper["location_ref"] = None
    paper["location"] = None

    # Process originatorPerson - convert list to list of refs
    if "originatorPerson" in paper and paper["originatorPerson"]:
        if isinstance(paper["originatorPerson"], list):
            paper["originatorPerson_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL)
                for url in paper["originatorPerson"]
            ]
        elif isinstance(paper["originatorPerson"], str):
            paper["originatorPerson_ref"] = [
                paper["originatorPerson"].replace(UPSTREAM_API_URL, SELF_API_URL)
            ]
        else:
            paper["originatorPerson_ref"] = None
    else:
        paper["originatorPerson_ref"] = None
    paper["originatorPerson"] = None

    # Process underDirectionOf - convert list to list of refs
    if "underDirectionOf" in paper and paper["underDirectionOf"]:
        if isinstance(paper["underDirectionOf"], list):
            paper["underDirectionOfPerson_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL)
                for url in paper["underDirectionOf"]
            ]
        elif isinstance(paper["underDirectionOf"], str):
            paper["underDirectionOfPerson_ref"] = [
                paper["underDirectionOf"].replace(UPSTREAM_API_URL, SELF_API_URL)
            ]
        else:
            paper["underDirectionOfPerson_ref"] = None
    else:
        paper["underDirectionOfPerson_ref"] = None
    paper["underDirectionOf"] = None

    # Process originatorOrganization - convert to list of refs
    if "originatorOrganization" in paper and paper["originatorOrganization"]:
        if isinstance(paper["originatorOrganization"], list):
            paper["originatorOrganization_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL)
                for url in paper["originatorOrganization"]
            ]
        elif isinstance(paper["originatorOrganization"], str):
            paper["originatorOrganization_ref"] = [
                paper["originatorOrganization"].replace(UPSTREAM_API_URL, SELF_API_URL)
            ]
        else:
            paper["originatorOrganization_ref"] = None
    else:
        paper["originatorOrganization_ref"] = None
    paper["originatorOrganization"] = None

    # Process consultation - list of objects with id fields
    if "consultation" in paper and paper["consultation"]:
        paper["consultation_ref"] = []
        for consultation in paper["consultation"]:
            if isinstance(consultation, dict) and "id" in consultation:
                paper["consultation_ref"].append(
                    consultation["id"].replace(UPSTREAM_API_URL, SELF_API_URL)
                )
            elif isinstance(consultation, str):
                paper["consultation_ref"].append(
                    consultation.replace(UPSTREAM_API_URL, SELF_API_URL)
                )
    else:
        paper["consultation_ref"] = None
    paper["consultation"] = None


def _process_membership(membership: dict) -> None:
    """Helper function to process membership data by converting URLs."""
    _update_id(membership)
    membership["person_ref"] = membership.get("person", None)
    if membership["person_ref"]:
        membership["person_ref"] = membership["person_ref"].replace(
            UPSTREAM_API_URL, SELF_API_URL
        )
    membership["person"] = None
    membership["organization_ref"] = membership.get("organization", None)
    if membership["organization_ref"]:
        membership["organization_ref"] = membership["organization_ref"].replace(
            UPSTREAM_API_URL, SELF_API_URL
        )
    membership["organization"] = None


def _process_meeting(m: dict) -> None:
    """Helper function to process Meeting data."""
    _update_id(m)

    # Process organization references
    _update_organization_attribute(m)

    # Process participant references
    if "participant" in m and m["participant"]:
        if isinstance(m["participant"], list):
            m["participant_ref"] = [
                url.replace(UPSTREAM_API_URL, SELF_API_URL) for url in m["participant"]
            ]
        elif isinstance(m["participant"], str):
            m["participant_ref"] = [
                m["participant"].replace(UPSTREAM_API_URL, SELF_API_URL)
            ]
        else:
            m["participant_ref"] = None
    else:
        m["participant_ref"] = None


def _process_person(person: dict) -> None:
    """Helper function to process person data by converting URLs."""
    _update_id(person)

    # Process membership references
    if "membership" in person:
        person["membership_ref"] = [
            membership["id"] for membership in person["membership"]
        ]
        # rewrite each membership URL
        person["membership_ref"] = [
            membership.replace(UPSTREAM_API_URL, SELF_API_URL)
            for membership in person["membership_ref"]
        ]
    else:
        person["membership_ref"] = None

    person["membership"] = None

    # Process location reference
    person["location_ref"] = person["location"] if "location" in person else None
    if person["location_ref"]:
        person["location_ref"] = person["location_ref"].replace(
            UPSTREAM_API_URL, SELF_API_URL
        )
    person["location"] = None


def _process_consultation(data: dict) -> None:
    """Process the consultation data to ensure it meets the expected format."""
    _update_id(data)

    # keywords?

    # process Paper references
    if "paper" in data and isinstance(data["paper"], str):
        data["paper_ref"] = data["paper"].replace(UPSTREAM_API_URL, SELF_API_URL)
        data["paper"] = None

    # process Meeting references
    if "meeting" in data and isinstance(data["meeting"], str):
        data["meeting_ref"] = data["meeting"].replace(UPSTREAM_API_URL, SELF_API_URL)
        data["meeting"] = None

    # process list of Organization references
    if "organization" in data and isinstance(data["organization"], list):
        data["organization_ref"] = [
            url.replace(UPSTREAM_API_URL, SELF_API_URL) for url in data["organization"]
        ]
        del data["organization"]
        data["organisations"] = []
