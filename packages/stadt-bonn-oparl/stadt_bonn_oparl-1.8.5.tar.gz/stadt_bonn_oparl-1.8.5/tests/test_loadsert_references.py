import json
from pyparsing import C
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
import chromadb
from chromadb.config import Settings

from stadt_bonn_oparl.api.helpers.processors import (
    _process_consultation,
    _process_meeting,
    _process_paper,
)
from stadt_bonn_oparl.tasks.consultations import (
    loadsert_references,
    load_paper,
    load_meeting,
)
from stadt_bonn_oparl.api.models import Consultation, PaperResponse, MeetingResponse


@pytest.fixture
def consultation_fixture():
    """Load the consultation fixture data."""
    with open("tests/fixtures/consultation_2030306_bi_2047328.json") as f:
        return json.load(f)


@pytest.fixture
def paper_fixture():
    """Load the paper fixture data."""
    with open("tests/fixtures/paper_2021241.json") as f:
        return json.load(f)


@pytest.fixture
def meeting_fixture():
    """Load the meeting fixture data."""
    with open("tests/fixtures/meeting_2004507.json") as f:
        return json.load(f)


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=httpx.Client)


@pytest.fixture
def mock_chromadb_client():
    """Create a mock ChromaDB client with collections."""
    client = Mock(spec=chromadb.PersistentClient)
    ccoll = Mock()
    pcoll = Mock()
    client.get_collection.side_effect = lambda name: (
        ccoll if name == "consultations" else pcoll
    )
    return client, ccoll, pcoll


class TestLoadPaper:
    """Test the load_paper function."""

    def test_load_paper_success(
        self, mock_http_client, paper_fixture, consultation_fixture
    ):
        """Test successful paper loading."""
        pcoll = Mock()
        _process_consultation(consultation_fixture)
        consultation = Consultation(**consultation_fixture)

        with (
            patch("stadt_bonn_oparl.tasks.consultations.asyncio.run") as mock_run,
            patch(
                "stadt_bonn_oparl.tasks.consultations._get_paper_by_id"
            ) as mock_get_paper,
        ):

            _process_paper(paper_fixture)
            mock_paper = PaperResponse(**paper_fixture)
            mock_run.return_value = mock_paper

            result = load_paper(mock_http_client, pcoll, consultation)

            assert result == mock_paper
            mock_get_paper.assert_called_once_with(mock_http_client, pcoll, "2021241")

    def test_load_paper_no_meeting_ref(self, mock_http_client, consultation_fixture):
        """Test paper loading when consultation has no meeting_ref."""
        pcoll = Mock()
        _process_consultation(consultation_fixture)
        consultation = Consultation(**consultation_fixture)

        result = load_paper(mock_http_client, pcoll, consultation)

        assert result is None


class TestLoadMeeting:
    """Test the load_meeting function."""

    def test_load_meeting_success(
        self, mock_http_client, meeting_fixture, consultation_fixture
    ):
        """Test successful meeting loading."""
        consultation = consultation_fixture

        with (
            patch("stadt_bonn_oparl.tasks.consultations.asyncio.run") as mock_run,
            patch(
                "stadt_bonn_oparl.tasks.consultations._get_meeting_by_id"
            ) as mock_get_meeting,
        ):

            _process_meeting(meeting_fixture)
            mock_meeting = MeetingResponse(**meeting_fixture)
            mock_run.return_value = mock_meeting

            _process_consultation(consultation_fixture)
            mock_consultation = Consultation(**consultation_fixture)
            result = load_meeting(mock_http_client, mock_consultation)

            assert result == mock_meeting
            mock_get_meeting.assert_called_once_with(mock_http_client, "2004507")

    def test_load_meeting_not_found(self, mock_http_client, consultation_fixture):
        """Test meeting loading when meeting is not found."""
        _process_consultation(consultation_fixture)
        consultation = Consultation(**consultation_fixture)

        with (
            patch("stadt_bonn_oparl.tasks.consultations.asyncio.run") as mock_run,
            patch(
                "stadt_bonn_oparl.tasks.consultations._get_meeting_by_id"
            ) as mock_get_meeting,
        ):

            mock_run.return_value = None

            with pytest.raises(ValueError, match="Meeting with id 2004507 not found"):
                load_meeting(mock_http_client, consultation)


class TestLoadsertReferences:
    """Test the main loadsert_references task function."""

    @patch("stadt_bonn_oparl.tasks.consultations.chromadb.PersistentClient")
    @patch("stadt_bonn_oparl.tasks.consultations.httpx.Client")
    @patch("stadt_bonn_oparl.tasks.consultations.load_meeting")
    @patch("stadt_bonn_oparl.tasks.consultations.load_paper")
    @patch("stadt_bonn_oparl.tasks.consultations.asyncio.run")
    def test_loadsert_references_success(
        self,
        mock_run,
        mock_load_paper,
        mock_load_meeting,
        mock_http_client,
        mock_chromadb_client,
        consultation_fixture,
        paper_fixture,
        meeting_fixture,
    ):
        """Test successful execution of loadsert_references."""
        # Setup mocks
        http_client = Mock()
        mock_http_client.return_value = http_client

        chromadb_client = Mock()
        ccoll = Mock()
        pcoll = Mock()
        chromadb_client.get_collection.side_effect = lambda name: (
            ccoll if name == "consultations" else pcoll
        )
        mock_chromadb_client.return_value = chromadb_client

        # Mock _get_consultation
        _process_consultation(consultation_fixture)
        consultation = Consultation(**consultation_fixture)
        mock_run.return_value = (True, consultation)

        # Mock load functions
        _process_paper(paper_fixture)
        paper = PaperResponse(**paper_fixture)
        mock_load_paper.return_value = paper
        _process_meeting(meeting_fixture)
        meeting = MeetingResponse(**meeting_fixture)
        mock_load_meeting.return_value = meeting

        # Execute
        result = loadsert_references(
            "https://www.bonn.sitzung-online.de/public/oparl/consultations?id=2030327&bi=2047329",
        )

        # Assertions
        assert result is True
        mock_load_paper.assert_called_once_with(http_client, pcoll, consultation)
        mock_load_meeting.assert_called_once_with(http_client, consultation)
        ccoll.upsert.assert_called_once()

        # Verify upsert call
        upsert_call = ccoll.upsert.call_args
        assert len(upsert_call[1]["documents"]) == 1
        assert upsert_call[1]["ids"] == [str(consultation.id)]

    @patch("stadt_bonn_oparl.tasks.consultations.chromadb.PersistentClient")
    @patch("stadt_bonn_oparl.tasks.consultations.httpx.Client")
    @patch("stadt_bonn_oparl.tasks.consultations.asyncio.run")
    def test_loadsert_references_consultation_not_found(
        self, mock_run, mock_http_client, mock_chromadb_client
    ):
        """Test when consultation is not found."""
        # Setup mocks
        http_client = Mock()
        mock_http_client.return_value = http_client

        chromadb_client = Mock()
        ccoll = Mock()
        pcoll = Mock()
        chromadb_client.get_collection.side_effect = lambda name: (
            ccoll if name == "consultations" else pcoll
        )
        mock_chromadb_client.return_value = chromadb_client

        # Mock _get_consultation to return None
        mock_run.return_value = (True, None)

        # Execute and expect ValueError
        with pytest.raises(ValueError, match="Consultation with ref .* not found"):
            loadsert_references(
                "https://www.bonn.sitzung-online.de/public/oparl/consultations?id=999999&bi=999999",
            )

    @patch("stadt_bonn_oparl.tasks.consultations.chromadb.PersistentClient")
    @patch("stadt_bonn_oparl.tasks.consultations.httpx.Client")
    @patch("stadt_bonn_oparl.tasks.consultations.load_meeting")
    @patch("stadt_bonn_oparl.tasks.consultations.load_paper")
    @patch("stadt_bonn_oparl.tasks.consultations.asyncio.run")
    def test_loadsert_references_paper_not_found(
        self,
        mock_run,
        mock_load_paper,
        mock_load_meeting,
        mock_http_client,
        mock_chromadb_client,
        consultation_fixture,
        meeting_fixture,
        caplog,
    ):
        """Test when paper is not found but meeting is found."""
        # Setup mocks
        http_client = Mock()
        mock_http_client.return_value = http_client

        chromadb_client = Mock()
        ccoll = Mock()
        pcoll = Mock()
        chromadb_client.get_collection.side_effect = lambda name: (
            ccoll if name == "consultations" else pcoll
        )
        mock_chromadb_client.return_value = chromadb_client

        # Mock _get_consultation
        consultation = Consultation(**consultation_fixture)
        mock_run.return_value = (True, consultation)

        # Mock load functions - paper fails, meeting succeeds
        mock_load_paper.return_value = None
        meeting = MeetingResponse(**meeting_fixture)
        mock_load_meeting.return_value = meeting

        # Execute
        result = loadsert_references(
            "https://www.bonn.sitzung-online.de/public/oparl/consultations?id=2030327&bi=2047329",
        )

        # Assertions
        assert result is True
        assert "Paper with ref 0 not found" in caplog.text
        ccoll.upsert.assert_called_once()

    @patch("stadt_bonn_oparl.tasks.consultations.chromadb.PersistentClient")
    @patch("stadt_bonn_oparl.tasks.consultations.httpx.Client")
    @patch("stadt_bonn_oparl.tasks.consultations.load_meeting")
    @patch("stadt_bonn_oparl.tasks.consultations.load_paper")
    @patch("stadt_bonn_oparl.tasks.consultations.asyncio.run")
    def test_loadsert_references_meeting_not_found(
        self,
        mock_run,
        mock_load_paper,
        mock_load_meeting,
        mock_http_client,
        mock_chromadb_client,
        consultation_fixture,
        paper_fixture,
        caplog,
    ):
        """Test when meeting is not found but paper is found."""
        # Setup mocks
        http_client = Mock()
        mock_http_client.return_value = http_client

        chromadb_client = Mock()
        ccoll = Mock()
        pcoll = Mock()
        chromadb_client.get_collection.side_effect = lambda name: (
            ccoll if name == "consultations" else pcoll
        )
        mock_chromadb_client.return_value = chromadb_client

        # Mock _get_consultation
        consultation = Consultation(**consultation_fixture)
        mock_run.return_value = (True, consultation)

        # Mock load functions - paper succeeds, meeting fails
        paper = PaperResponse(**paper_fixture)
        mock_load_paper.return_value = paper
        mock_load_meeting.return_value = None

        # Execute
        result = loadsert_references(
            "https://www.bonn.sitzung-online.de/public/oparl/consultations?id=2030327&bi=2047329",
        )

        # Assertions
        assert result is True
        assert "Meeting with ref" in caplog.text and "not found" in caplog.text
        ccoll.upsert.assert_called_once()

    @patch("stadt_bonn_oparl.tasks.consultations.chromadb.PersistentClient")
    @patch("stadt_bonn_oparl.tasks.consultations.httpx.Client")
    @patch("stadt_bonn_oparl.tasks.consultations.load_meeting")
    @patch("stadt_bonn_oparl.tasks.consultations.load_paper")
    @patch("stadt_bonn_oparl.tasks.consultations.asyncio.run")
    def test_loadsert_references_both_not_found(
        self,
        mock_run,
        mock_load_paper,
        mock_load_meeting,
        mock_http_client,
        mock_chromadb_client,
        consultation_fixture,
        caplog,
    ):
        """Test when both paper and meeting are not found."""
        # Setup mocks
        http_client = Mock()
        mock_http_client.return_value = http_client

        chromadb_client = Mock()
        ccoll = Mock()
        pcoll = Mock()
        chromadb_client.get_collection.side_effect = lambda name: (
            ccoll if name == "consultations" else pcoll
        )
        mock_chromadb_client.return_value = chromadb_client

        # Mock _get_consultation
        consultation = Consultation(**consultation_fixture)
        mock_run.return_value = (True, consultation)

        # Mock load functions to return None
        mock_load_paper.return_value = None
        mock_load_meeting.return_value = None

        # Execute
        result = loadsert_references(
            "https://www.bonn.sitzung-online.de/public/oparl/consultations?id=2030327&bi=2047329",
        )

        # Assertions
        assert result is True
        ccoll.upsert.assert_called_once()
