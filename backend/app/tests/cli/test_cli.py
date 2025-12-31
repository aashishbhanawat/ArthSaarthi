import uuid

import pytest
from typer.testing import CliRunner

from run_cli import app as main_app

runner = CliRunner()

# Mock data for testing
MOCK_NSDL_TSV = """ISIN\tNAME_OF_THE_INSTRUMENT\tREDEMPTION\tFACE_VALUE\tCOUPON_RATE
INE001\tBOND A\t01-01-2030\t1000\t8.5
"""

MOCK_BSE_EQUITY_CSV = """ISIN,TckrSymb,FinInstrmNm,SctySrs
INE002,STOCKB,STOCK B,A
"""

@pytest.fixture
def mock_db_session_empty(mocker):
    """Mocks the database session to return no existing assets."""
    mock_db_session_context = mocker.patch("app.cli.get_db_session")
    mock_db = mock_db_session_context.return_value.__next__.return_value
    mock_query_object = mocker.Mock()
    mock_query_object.filter.return_value.all.return_value = []  # for isin
    # For enrich_assets: .filter(...).limit(...).all()
    mock_query_object.filter.return_value.limit.return_value.all.return_value = []
    mock_query_object.all.return_value = []  # for ticker
    mock_db.query.return_value = mock_query_object
    # Also need inspector
    mocker.patch("sqlalchemy.inspect").return_value.has_table.return_value = True
    return mock_db


def test_seed_assets_with_local_dir(mocker, tmp_path, mock_db_session_empty):
    """Tests seeding from a local directory."""
    # Create mock local files
    (tmp_path / "nsdl_debt.xls").write_text(MOCK_NSDL_TSV)
    (tmp_path / "bse_equity.csv").write_text(MOCK_BSE_EQUITY_CSV)

    # Mock crud.asset.create
    mock_asset = mocker.Mock()
    mock_asset.id = uuid.uuid4() # Use real UUID
    mock_asset.asset_type = "STOCK"
    mock_asset_create = mocker.patch("app.crud.asset.create", return_value=mock_asset)
    mocker.patch("app.crud.bond.create")

    # Run the command
    result = runner.invoke(
        main_app, ["db", "seed-assets", "--local-dir", str(tmp_path), "--debug"]
    )

    # Assertions
    assert result.exit_code == 0
    assert "Searching for files in" in result.stdout
    assert "Processing NSDL file" in result.stdout
    assert "Processing BSE Equity Bhavcopy" in result.stdout
    assert "Total assets created: 2" in result.stdout

    assert mock_asset_create.call_count == 2


@pytest.fixture
def mock_db_session_with_data(mocker):
    """Mocks the database session for the clear command."""
    mock_db_session_context = mocker.patch("app.cli.get_db_session")
    mock_db = mock_db_session_context.return_value.__next__.return_value

    def query_side_effect(model):
        # Create a new mock for each query to handle chained calls
        mock_query = mocker.Mock()
        # Set a default return value for delete()
        mock_query.delete.return_value = 0
        # Set specific return values for models we are testing against
        if model.__name__ == "Transaction":
            mock_query.delete.return_value = 5  # 5 transactions deleted
        elif model.__name__ == "Portfolio":
            mock_query.delete.return_value = 2  # 2 portfolios deleted
        elif model.__name__ == "Asset":
            mock_query.delete.return_value = 10  # 10 assets deleted
        # For any other model, it will return 0, and no message will be printed.
        return mock_query

    mock_db.query.side_effect = query_side_effect

    return mock_db


def test_clear_assets_with_confirmation(mocker, mock_db_session_with_data):
    """Tests the clear-assets command with user confirmation."""
    result = runner.invoke(main_app, ["db", "clear-assets"], input="y\n") # noqa: E501
    print(
        f"\n--- STDOUT for test_clear_assets_with_confirmation ---\n{result.stdout}\n"
        "----------------------------------------------------"
    )

    assert result.exit_code == 0
    assert "Are you sure you want to proceed?" in result.stdout  # noqa: E501
    assert "Deleted 5 rows from transactions." in result.stdout
    assert "Deleted 2 rows from portfolios." in result.stdout
    assert "Deleted 10 rows from assets." in result.stdout
    assert mock_db_session_with_data.commit.call_count == 1


def test_clear_assets_with_force(mocker, mock_db_session_with_data):
    """Tests the clear-assets command with the --force flag."""
    result = runner.invoke(main_app, ["db", "clear-assets", "--force"]) # noqa: E501
    print(
        f"\n--- STDOUT for test_clear_assets_with_force ---\n{result.stdout}\n"
        "-------------------------------------------------"
    )

    assert result.exit_code == 0
    assert "Are you sure you want to proceed?" not in result.stdout  # noqa: E501
    assert "Deleted 5 rows from transactions." in result.stdout
    assert "Deleted 2 rows from portfolios." in result.stdout
    assert "Deleted 10 rows from assets." in result.stdout
    assert mock_db_session_with_data.commit.call_count == 1
