import pytest
from unittest.mock import patch, Mock
from nmdc_mcp.api import fetch_nmdc_biosample_records_paged


@pytest.fixture
def mock_response():
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "resources": [{"id": "sample1"}, {"id": "sample2"}],
        "next_page_token": None,
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_fetch_nmdc_biosample_records_paged(mock_response):
    with patch("requests.get", return_value=mock_response):
        results = fetch_nmdc_biosample_records_paged(max_page_size=10)

    assert len(results) == 2
    assert results[0]["id"] == "sample1"
    assert results[1]["id"] == "sample2"
