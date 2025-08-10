import io
import zipfile

import pytest
from typer.testing import CliRunner

from run_cli import app as main_app

runner = CliRunner()

# Mock data for testing
MOCK_NSE_CSV = """\
"Token","CompanyName","Series","ExchangeCode","ISINCode"
"1","NSE_COMPANY_A","EQ","NSEA","INE001A01010"
"2","NSE_COMPANY_B","BE","NSEB","INE002A01010"
"3","NSE_COMPANY_C","XX","NSEC","INE003A01010"
"""

MOCK_BSE_CSV = """\
"Token","CompanyName","Series","ScripID","ISINCode"
"4","BSE_COMPANY_D","A","BSED","INE004A01010"
"5","BSE_COMPANY_E","B","BSEE","INE005A01010"
"6","BSE_COMPANY_F","DR","BSEF","INE006A01010"
"""


def create_mock_zip():
    """Creates an in-memory zip file containing mock CSV data."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("NSEScripMaster.txt", MOCK_NSE_CSV)
        zf.writestr("BSEScripMaster.txt", MOCK_BSE_CSV)
    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def mock_db_session_empty(mocker):
    """Mocks the database session to return no existing assets."""
    mock_db_session_context = mocker.patch("app.cli.get_db_session")
    mock_db = mock_db_session_context.return_value.__next__.return_value
    mock_query_object = mocker.Mock()
    mock_query_object.filter.return_value.all.return_value = []  # for isin
    mock_query_object.all.return_value = []  # for ticker
    mock_db.query.return_value = mock_query_object
    return mock_db


def test_seed_assets_from_url(mocker, mock_db_session_empty):
    """Tests seeding from a (mocked) downloaded zip file."""
    # Mock requests.get
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = create_mock_zip()
    mocker.patch("requests.get", return_value=mock_response)

    mock_asset_create = mocker.patch("app.crud.asset.create", return_value=None)

    # Run the command
    result = runner.invoke(main_app, ["db", "seed-assets"])

    # Assertions
    assert result.exit_code == 0
    assert "Downloading security master file" in result.stdout
    assert "NSE processing complete. Created: 2, Skipped: 0" in result.stdout
    assert "BSE processing complete. Created: 2, Skipped: 0" in result.stdout
    assert "Total assets created: 4" in result.stdout
    assert "Series 'XX': 1 rows skipped" in result.stdout
    assert "Series 'DR': 1 rows skipped" in result.stdout
    assert mock_asset_create.call_count == 4

    # Check one of the calls for correctness
    first_call_args = mock_asset_create.call_args_list[0].kwargs["obj_in"]
    assert first_call_args.ticker_symbol == "NSEA"
    assert first_call_args.name == "NSE_COMPANY_A"


def test_seed_assets_with_local_dir(mocker, tmp_path, mock_db_session_empty):
    """Tests seeding from a local directory."""
    # Create mock local files
    (tmp_path / "NSEScripMaster.txt").write_text(MOCK_NSE_CSV)
    (tmp_path / "BSEScripMaster.txt").write_text(MOCK_BSE_CSV)

    mock_asset_create = mocker.patch("app.crud.asset.create", return_value=None)

    # Run the command
    result = runner.invoke(
        main_app, ["db", "seed-assets", "--local-dir", str(tmp_path)]
    )

    # Assertions
    assert result.exit_code == 0
    assert "Processing local files from" in result.stdout
    assert "NSE processing complete. Created: 2, Skipped: 0" in result.stdout
    assert "BSE processing complete. Created: 2, Skipped: 0" in result.stdout
    assert "Total assets created: 4" in result.stdout
    assert mock_asset_create.call_count == 4


@pytest.fixture
def mock_db_session_with_data(mocker):
    """Mocks the database session for the clear command."""
    mock_db_session_context = mocker.patch("app.cli.get_db_session")
    mock_db = mock_db_session_context.return_value.__next__.return_value

    # Mock the delete calls
    mock_query_object = mocker.Mock()

    def query_side_effect(model):
        if model.__name__ == "Transaction":
            mock_query_object.delete.return_value = 5  # 5 transactions deleted
        elif model.__name__ == "Portfolio":
            mock_query_object.delete.return_value = 2  # 2 portfolios deleted
        elif model.__name__ == "Asset":
            mock_query_object.delete.return_value = 10  # 10 assets deleted
        return mock_query_object

    mock_db.query.side_effect = query_side_effect

    return mock_db


def test_clear_assets_with_confirmation(mocker, mock_db_session_with_data):
    """Tests the clear-assets command with user confirmation."""
    result = runner.invoke(main_app, ["db", "clear-assets"], input="y\n")

    assert result.exit_code == 0
    assert "Are you sure you want to proceed?" in result.stdout
    assert "Successfully deleted 5 transactions." in result.stdout
    assert "Successfully deleted 2 portfolios." in result.stdout
    assert "Successfully deleted 10 assets." in result.stdout
    assert mock_db_session_with_data.commit.call_count == 1


def test_clear_assets_with_force(mocker, mock_db_session_with_data):
    """Tests the clear-assets command with the --force flag."""
    result = runner.invoke(main_app, ["db", "clear-assets", "--force"])

    assert result.exit_code == 0
    assert "Are you sure you want to proceed?" not in result.stdout
    assert "Successfully deleted 5 transactions." in result.stdout
    assert "Successfully deleted 2 portfolios." in result.stdout
    assert "Successfully deleted 10 assets." in result.stdout
    assert mock_db_session_with_data.commit.call_count == 1
