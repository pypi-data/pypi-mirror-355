import os
from unittest.mock import patch

import pandas as pd
import pytest

# Add the project root directory to the Python path to fix import issues
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dataslicer.main import main


@pytest.fixture
def temp_csv(tmp_path):
    """Creates a temporary CSV file with test data."""
    temp_file = tmp_path / "test_file.csv"
    test_content = """Name,Department,Salary
Alice,HR,50000
Bob,IT,60000
Charlie,HR,55000
David,IT,70000
"""
    temp_file.write_text(test_content)
    return str(temp_file)


@pytest.fixture
def temp_excel(tmp_path):
    """Creates a temporary Excel file with test data."""
    temp_file = tmp_path / "test_file.xlsx"
    df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie", "David"],
            "Department": ["HR", "IT", "HR", "IT"],
            "Salary": [50000, 60000, 55000, 70000],
        }
    )
    df.to_excel(temp_file, index=False)
    return str(temp_file)


@pytest.fixture
def temp_folder_with_files(tmp_path):
    """Creates a temporary folder with multiple CSV and Excel files having the same columns."""
    folder = tmp_path / "test_folder"
    folder.mkdir()

    # Create first CSV file
    csv1 = folder / "file1.csv"
    csv1.write_text("""Name,Department,Salary
Alice,HR,50000
Bob,IT,60000""")

    # Create second CSV file
    csv2 = folder / "file2.csv"
    csv2.write_text("""Name,Department,Salary
Charlie,HR,55000
David,IT,70000""")

    # Create Excel file
    excel1 = folder / "file1.xlsx"
    df = pd.DataFrame({"Name": ["Eva", "Frank"], "Department": ["Marketing", "Finance"], "Salary": [65000, 75000]})
    df.to_excel(excel1, index=False)

    return str(folder)


@pytest.fixture
def temp_folder_with_inconsistent_files(tmp_path):
    """Creates a temporary folder with files having inconsistent columns."""
    folder = tmp_path / "inconsistent_folder"
    folder.mkdir()

    # Create first file with standard columns
    csv1 = folder / "file1.csv"
    csv1.write_text("""Name,Department,Salary
Alice,HR,50000
Bob,IT,60000""")

    # Create second file with different columns
    csv2 = folder / "file2.csv"
    csv2.write_text("""Name,Role,Income
Charlie,Manager,55000
David,Developer,70000""")

    return str(folder)


def test_main_csv_workflow(temp_csv, tmp_path, monkeypatch):
    """Test the complete workflow of main() with CSV input and output."""
    export_folder = str(tmp_path / "exports")
    os.makedirs(export_folder, exist_ok=True)

    # Mock the inputs using patch for input function
    with patch(
        "builtins.input",
        side_effect=[
            temp_csv,  # file path
            "2",  # select Department column
            "",  # finish column selection
            "2",  # select Department for filename
            export_folder,  # export folder
            "2",  # choose CSV format
        ],
    ):
        # Run the main function
        main()

    # Check that the expected files were created
    hr_file = os.path.join(export_folder, "HR", "HR.csv")
    it_file = os.path.join(export_folder, "IT", "IT.csv")

    assert os.path.exists(hr_file), f"HR file was not created at {hr_file}"
    assert os.path.exists(it_file), f"IT file was not created at {it_file}"

    # Verify content of HR file
    hr_df = pd.read_csv(hr_file)
    assert len(hr_df) == 2
    assert "Alice" in list(hr_df["Name"]) and "Charlie" in list(hr_df["Name"])

    # Verify content of IT file
    it_df = pd.read_csv(it_file)
    assert len(it_df) == 2
    assert "Bob" in list(it_df["Name"]) and "David" in list(it_df["Name"])


def test_main_excel_workflow(temp_excel, tmp_path, monkeypatch):
    """Test the complete workflow of main() with Excel input and output."""
    export_folder = str(tmp_path / "exports_excel")
    os.makedirs(export_folder, exist_ok=True)

    # Mock the inputs using patch for input function
    with patch(
        "builtins.input",
        side_effect=[
            temp_excel,  # file path
            "2",  # select Department column
            "",  # finish column selection
            "2",  # select Department for filename
            export_folder,  # export folder
            "1",  # choose Excel format
        ],
    ):
        # Run the main function
        main()

    # Check that the expected files were created
    hr_file = os.path.join(export_folder, "HR", "HR.xlsx")
    it_file = os.path.join(export_folder, "IT", "IT.xlsx")

    assert os.path.exists(hr_file), f"HR file was not created at {hr_file}"
    assert os.path.exists(it_file), f"IT file was not created at {it_file}"

    # Verify content of HR file
    hr_df = pd.read_excel(hr_file)
    assert len(hr_df) == 2
    assert "Alice" in list(hr_df["Name"]) and "Charlie" in list(hr_df["Name"])

    # Verify content of IT file
    it_df = pd.read_excel(it_file)
    assert len(it_df) == 2
    assert "Bob" in list(it_df["Name"]) and "David" in list(it_df["Name"])


def test_main_with_custom_filename(temp_csv, tmp_path, monkeypatch):
    """Test the workflow with a custom filename option."""
    export_folder = str(tmp_path / "exports_custom")
    os.makedirs(export_folder, exist_ok=True)

    # Mock the inputs using patch for input function
    with patch(
        "builtins.input",
        side_effect=[
            temp_csv,  # file path
            "2",  # select Department column
            "",  # finish column selection
            "0",  # select custom filename
            "test_export",  # custom filename
            export_folder,  # export folder
            "2",  # choose CSV format
        ],
    ):
        # Run the main function
        main()

    # Check that the expected files were created
    hr_file = os.path.join(export_folder, "HR", "test_export.csv")
    it_file = os.path.join(export_folder, "IT", "test_export.csv")

    assert os.path.exists(hr_file), f"HR file was not created at {hr_file}"
    assert os.path.exists(it_file), f"IT file was not created at {it_file}"


def test_main_with_multiple_group_columns(temp_csv, tmp_path, monkeypatch):
    """Test grouping by multiple columns."""
    export_folder = str(tmp_path / "exports_multi")
    os.makedirs(export_folder, exist_ok=True)

    # Mock the inputs using patch for input function
    with patch(
        "builtins.input",
        side_effect=[
            temp_csv,  # file path
            "1",  # select Name column (index 1 initially)
            "1",  # select Department column (now index 1 after Name was removed)
            "",  # finish column selection
            "3",  # select Salary for filename (now index 1 in remaining columns)
            export_folder,  # export folder
            "2",  # choose CSV format
        ],
    ):
        # Run the main function
        main()

    # Check that the expected nested folder structure was created
    # With Name then Department grouping, and using Salary for filename
    paths = [
        os.path.join(export_folder, "Alice", "HR", "50000.csv"),
        os.path.join(export_folder, "Bob", "IT", "60000.csv"),
        os.path.join(export_folder, "Charlie", "HR", "55000.csv"),
        os.path.join(export_folder, "David", "IT", "70000.csv"),
    ]

    for path in paths:
        assert os.path.exists(path), f"File was not created at {path}"


def test_main_folder_with_consistent_files(temp_folder_with_files, tmp_path, monkeypatch):
    """Test the workflow with a folder containing multiple files with consistent columns."""
    export_folder = str(tmp_path / "exports_folder")
    os.makedirs(export_folder, exist_ok=True)

    # Mock the inputs
    with patch(
        "builtins.input",
        side_effect=[
            temp_folder_with_files,  # folder path
            "2",  # select Department column
            "",  # finish column selection
            "2",  # select Department for filename
            export_folder,  # export folder
            "2",  # choose CSV format
        ],
    ):
        # Run the main function
        main()

    # Check that the expected files were created with combined data
    hr_file = os.path.join(export_folder, "HR", "HR.csv")
    it_file = os.path.join(export_folder, "IT", "IT.csv")
    marketing_file = os.path.join(export_folder, "Marketing", "Marketing.csv")
    finance_file = os.path.join(export_folder, "Finance", "Finance.csv")

    assert os.path.exists(hr_file), f"HR file was not created at {hr_file}"
    assert os.path.exists(it_file), f"IT file was not created at {it_file}"
    assert os.path.exists(marketing_file), f"Marketing file was not created at {marketing_file}"
    assert os.path.exists(finance_file), f"Finance file was not created at {finance_file}"

    # Verify content
    hr_df = pd.read_csv(hr_file)
    assert len(hr_df) == 2
    assert "Alice" in list(hr_df["Name"]) and "Charlie" in list(hr_df["Name"])

    it_df = pd.read_csv(it_file)
    assert len(it_df) == 2
    assert "Bob" in list(it_df["Name"]) and "David" in list(it_df["Name"])


def test_main_folder_with_inconsistent_files(temp_folder_with_inconsistent_files, monkeypatch):
    """Test that an error is raised when processing a folder with inconsistent columns."""
    # Mock the inputs
    with patch("builtins.input", return_value=temp_folder_with_inconsistent_files):
        # The function should raise an error because of inconsistent columns
        with pytest.raises(Exception) as excinfo:
            main()

        # Verify the error message contains information about column inconsistency
        assert "different columns" in str(excinfo.value).lower() or "column" in str(excinfo.value).lower()
