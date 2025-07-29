import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

from . import __version__

load_dotenv()


# OParl API configuration
OPARL_BASE_URL = "http://localhost:8000"
UPSTREAM_API_URL = "https://www.bonn.sitzung-online.de/public/oparl"

OPARL_PAPERS_ENDPOINT = "/papers?body=1"
OPARL_MAX_PAGES = 5  # Limit number of pages to fetch (20 items per page)

# Application settings
USER_AGENT = f"stadt-bonn-ratsinfo/{__version__} (https://machdenstaat.de)"

CACHE_DIR = Path(".") / ".cache" / "oparl_responses"
DEFAULT_DATA_PATH = Path("./data")

# Celery configuration
# read from environment variable or use default
BROKER_URL = os.environ.get("BROKER_URL", "amqp://guest@localhost")


# CLI queryable OParl types
class CLI_QUERYABLE_OPARL_TYPES(str, Enum):
    """Queryable OParl types for CLI commands."""

    # PAPER = "Paper"
    ORGANIZATION = "Organization"
    # PERSON = "Person"
    # MEETING = "Meeting"
    # AGENDA_ITEM = "AgendaItem"
    # FILE = "File"
    # LOCATION = "Location"
    # CONSULTATION = "Consultation"
    # MEMBERSHIP = "Membership"
    # BODY = "Body"
    # DOCUMENT = "Document"
