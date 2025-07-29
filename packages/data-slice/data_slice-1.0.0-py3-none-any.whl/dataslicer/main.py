import os
from typing import Any, Union

import pandas as pd
from pathvalidate import sanitize_filename, sanitize_filepath
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def get_file_path() -> str:
    """Ask the user for the file path, which can be a file or directory."""
    while True:
        file_path: str = Prompt.ask(
            "[bold cyan]Enter the path to your Excel/CSV file or folder containing multiple files[/]"
        ).strip()

        # Strip quotes if present (handles both single and double quotes)
        if (file_path.startswith('"') and file_path.endswith('"')) or (
            file_path.startswith("'") and file_path.endswith("'")
        ):
            file_path = file_path[1:-1]

        if os.path.isfile(file_path) or os.path.isdir(file_path):
            return file_path
        else:
            console.print("[bold red]Path does not exist. Please try again.[/]")


def read_file(file_path: str) -> pd.DataFrame:
    """
    Read a single file or all Excel and CSV files in a directory.
    Ensures all files in a directory have consistent columns.
    """
    if os.path.isfile(file_path):
        # Handle single file
        _, ext = os.path.splitext(file_path)
        if ext.lower() == ".csv":
            df = pd.read_csv(file_path)
        elif ext.lower() in [".xls", ".xlsx"]:
            df = pd.read_excel(file_path, sheet_name=0)
        else:
            raise ValueError("[bold red]Unsupported file type. Please provide a CSV or Excel file.[/]")
        return df

    elif os.path.isdir(file_path):
        # Handle directory
        console.print(f"[bold cyan]Reading files from directory: {file_path}[/]")
        all_dfs = []
        columns = None

        # Get list of CSV and Excel files
        files = [f for f in os.listdir(file_path) if f.lower().endswith((".csv", ".xls", ".xlsx"))]

        if not files:
            raise ValueError("[bold red]No CSV or Excel files found in the directory.[/]")

        for file in files:
            full_path = os.path.join(file_path, file)
            _, ext = os.path.splitext(file)

            try:
                if ext.lower() == ".csv":
                    df = pd.read_csv(full_path)
                else:  # Excel files
                    df = pd.read_excel(full_path, sheet_name=0)

                # Check if columns are consistent
                if columns is None:
                    columns = set(df.columns)
                elif set(df.columns) != columns:
                    raise ValueError(
                        f"[bold red]File '{file}' has different columns than other files. "
                        f"All files must have the same columns.[/]"
                    )

                all_dfs.append(df)
                console.print(f"[green]Successfully read: {file}[/]")
            except Exception as e:
                raise ValueError(f"[bold red]Error reading file '{file}': {e!s}[/]") from e

        if not all_dfs:
            raise ValueError("[bold red]No valid files could be read from the directory.[/]")

        # Combine all dataframes
        combined_df = pd.concat(all_dfs, ignore_index=True)
        console.print(f"[bold green]Successfully combined {len(all_dfs)} files with {len(combined_df)} total rows.[/]")

        return combined_df

    else:
        raise ValueError("[bold red]The path is neither a file nor a directory.[/]")


def choose_columns(columns: list[str]) -> list[str]:
    """
    Let the user select columns by number.
    The selection order will determine the folder hierarchy.
    """
    selected_columns: list[str] = []
    available: list[str] = list(columns)  # Copy of the list to show available columns

    while True:
        table = Table(title="Available columns to split by (order matters)", show_lines=True)
        table.add_column("#", justify="right", style="bold")
        table.add_column("Column Name", style="cyan")

        for i, col in enumerate(available, start=1):
            table.add_row(str(i), col)

        console.print(table)
        choice: str = Prompt.ask("[bold yellow]Select a column by number (or press Enter to finish)[/]").strip()

        if choice == "":
            if not selected_columns:
                console.print("[bold red]You must select at least one column.[/]")
                continue
            else:
                break
        try:
            num: int = int(choice)
            if num < 1 or num > len(available):
                console.print("[bold red]Invalid selection. Try again.[/]")
                continue
            selected_col: str = available.pop(num - 1)
            selected_columns.append(selected_col)
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a valid number.[/]")

    return selected_columns


def choose_filename_column(columns: list[str]) -> str:
    """
    Let the user select a column to use for the filename or enter a custom string.
    """
    table = Table(title="Available columns for filename", show_lines=True)
    table.add_column("#", justify="right", style="bold")
    table.add_column("Column Name", style="cyan")

    for i, col in enumerate(columns, start=1):
        table.add_row(str(i), col)
    table.add_row("0", "[bold yellow]Enter a custom string[/]")

    console.print(table)

    while True:
        choice: str = Prompt.ask(
            "[bold yellow]Select a column for the filename by number or enter 0 for a custom string[/]"
        ).strip()
        try:
            num: int = int(choice)
            if num == 0:
                custom_string = Prompt.ask("[bold yellow]Enter the custom string for the filename[/]").strip()
                return f"custom:{custom_string}"
            elif num < 1 or num > len(columns):
                console.print("[bold red]Invalid selection. Try again.[/]")
                continue
            return columns[num - 1]
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a valid number.[/]")


def get_export_folder() -> str:
    """
    Keep asking for an export folder until a valid path is provided.
    If the folder doesn't exist, try to create it.
    """
    while True:
        folder: str = Prompt.ask("[bold cyan]Enter the path to the export folder[/]").strip()

        # Strip quotes if present
        if (folder.startswith('"') and folder.endswith('"')) or (folder.startswith("'") and folder.endswith("'")):
            folder = folder[1:-1]

        if folder:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                    console.print(f"[bold green]Folder '{folder}' created.[/]")
                except Exception as e:
                    console.print(f"[bold red]Could not create folder: {e}[/]")
                    continue
            return folder
        else:
            console.print("[bold red]You must enter a valid folder path.[/]")


def choose_export_format() -> str:
    """
    Ask the user to choose an export format by number:
    1. Excel
    2. CSV
    """
    console.print("\n[bold yellow]Choose export format:[/]")
    console.print("[bold]1.[/] Excel")
    console.print("[bold]2.[/] CSV")

    while True:
        choice: str = Prompt.ask("[bold cyan]Enter the number of the export format[/]").strip()
        if choice == "1":
            return "excel"
        elif choice == "2":
            return "csv"
        else:
            console.print("[bold red]Invalid selection. Please enter 1 or 2.[/]")


def save_group(
    df: pd.DataFrame,
    group_keys: Union[Any, tuple[Any, ...]],
    selected_columns: list[str],
    filename_column: str,
    export_folder: str,
    export_format: str,
) -> None:
    """
    Create the nested folder structure based on group_keys and save the subset file.
    The output filename is based on the value of the filename_column for this group.
    """
    subfolder_path: str = export_folder
    # Build the folder structure in the order of grouping (not reversed)
    if not isinstance(group_keys, tuple):
        group_keys = (group_keys,)
    for key in group_keys:
        subfolder_path = sanitize_filepath(os.path.join(subfolder_path, sanitize_filename(str(key))))
    os.makedirs(subfolder_path, exist_ok=True)

    # Use the custom string if provided, otherwise use the filename column value
    if filename_column.startswith("custom:"):
        raw_filename = sanitize_filename(filename_column[len("custom:") :])
    elif filename_column in df.columns:
        # Use the first value in the group for the filename column
        filename_value = str(df[filename_column].iloc[0])
        raw_filename = sanitize_filename(filename_value)
    else:
        # Fallback to the old behavior if the filename column doesn't exist
        filename_parts: list[str] = [str(val) for val in reversed(group_keys)]
        raw_filename = " - ".join(filename_parts)
        raw_filename = sanitize_filename(raw_filename)

    # Append the file extension
    file_extension: str = ".xlsx" if export_format == "excel" else ".csv"
    file_name: str = raw_filename + file_extension
    file_path: str = os.path.join(subfolder_path, file_name)

    # Save the file in the chosen format
    if export_format == "excel":
        df.to_excel(file_path, index=False)
    else:
        df.to_csv(file_path, index=False)

    console.print(f"[bold green]Saved group {group_keys} to {file_path}[/]")


def main() -> None:
    console.print("[bold cyan]Welcome to the File Splitter![/]")

    # Get the input file and load it into a DataFrame
    file_path: str = get_file_path()
    df: pd.DataFrame = read_file(file_path)

    # Display the available columns
    console.print("\n[bold cyan]Columns in the file:[/]")
    table = Table(title="Available Columns", show_lines=True)
    table.add_column("#", justify="right", style="bold")
    table.add_column("Column Name", style="cyan")

    for i, col in enumerate(df.columns, start=1):
        table.add_row(str(i), col)

    console.print(table)

    # Let the user choose the columns (in order) for splitting
    split_columns: list[str] = choose_columns(df.columns.tolist())
    console.print("\n[bold yellow]Selected columns (in order):[/]", split_columns)

    # Let the user choose a column for the filename
    filename_column: str = choose_filename_column(df.columns.tolist())
    console.print(f"\n[bold yellow]Column selected for filename:[/] {filename_column}")

    # Ask for export folder and export format
    export_folder: str = get_export_folder()
    export_format: str = choose_export_format()

    # Group the DataFrame by the selected columns and export each group
    grouped = df.groupby(split_columns)
    console.print("\n[bold cyan]Splitting file and exporting groups...[/]")
    for group_keys, group_df in grouped:
        save_group(group_df, group_keys, split_columns, filename_column, export_folder, export_format)

    console.print("[bold green]All groups exported successfully![/]")


if __name__ == "__main__":
    main()
