import orjson
import difflib
from datetime import datetime
from typing import List, Optional, Any

import typer
from sqlmodel import Session, create_engine, select
from rich.console import Console

from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy

console = Console()


def get_section_dict(section: Any) -> Optional[dict]:
    """Convert a section to a dictionary for comparison."""
    if section is None:
        return None
    if isinstance(section, dict):
        return section
    if hasattr(section, "model_dump"):
        return section.model_dump(mode="json")
    return None


def exclude_version_fields(data: Optional[dict]) -> Optional[dict]:
    """
    Remove fields that represent version metadata rather than content changes.
    
    Specifically excludes:
    - miscInfoModule.versionHolder: API's internal version timestamp
    """
    if data is None:
        return None
    
    # Make a deep copy to avoid modifying the original
    import copy
    cleaned = copy.deepcopy(data)
    
    # Remove miscInfoModule.versionHolder if it exists
    if "miscInfoModule" in cleaned and isinstance(cleaned["miscInfoModule"], dict):
        if "versionHolder" in cleaned["miscInfoModule"]:
            del cleaned["miscInfoModule"]["versionHolder"]
    
    return cleaned


def format_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return "Unknown Date"
    return dt.strftime("%Y-%m-%d")


def generate_diff(
    old_content: dict, new_content: dict, context_lines: int = 3
) -> List[str]:
    """Generate a unified diff between two dictionaries."""

    # Dump to pretty-printed JSON strings
    old_str = orjson.dumps(old_content, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2).decode("utf-8")
    new_str = orjson.dumps(new_content, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2).decode("utf-8")

    old_lines = old_str.splitlines()
    new_lines = new_str.splitlines()

    return list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="Previous Version",
            tofile="New Version",
            n=context_lines,
            lineterm="",
        )
    )


def print_diff(diff_lines: List[str]):
    """Print the diff with syntax highlighting."""
    if not diff_lines:
        return

    # Join lines and print using rich for coloring
    # Simple color coding based on diff markers
    for line in diff_lines:
        if line.startswith("---") or line.startswith("+++"):
            console.print(line, style="bold")
        elif line.startswith("@@"):
            console.print(line, style="cyan")
        elif line.startswith("+"):
            console.print(line, style="green")
        elif line.startswith("-"):
            console.print(line, style="red")
        else:
            console.print(line)


def diff_study_command(
    nct_id: str = typer.Argument(
        ..., help="The NCT ID of the study to inspect (e.g., NCT01234567)"
    ),
    url: str = typer.Option(
        None,
        "--url",
        help="Database connection URL (defaults to DATABASE_URL env var)",
        envvar="DATABASE_URL",
    ),
    full: bool = typer.Option(
        False, "--full", help="Show full content instead of just diffs"
    ),
) -> None:
    """
    Show changes between versions of a clinical trial.
    """
    # Use default if no URL provided
    if not url:
        url = (
            "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/"
            "clinical_aithena"
        )

    try:
        engine = create_engine(url, echo=False)

        with Session(engine) as session:
            # Fetch all versions of the study, sorted by version_date
            statement = (
                select(CTGovStudy)
                .where(CTGovStudy.nct_id == nct_id)
                .order_by(CTGovStudy.version_date)
            )
            studies = session.exec(statement).all()

            if not studies:
                console.print(
                    f"[bold red]No studies found with NCT ID: {nct_id}[/bold red]"
                )
                raise typer.Exit(code=1)

            console.print(
                f"[bold blue]Found {len(studies)} versions for {nct_id}[/bold blue]"
            )

            # Print basic info for each version
            for i, study in enumerate(studies):
                is_latest_str = " (Latest)" if study.is_latest else ""
                console.print(
                    f"Version {i+1}: {format_date(study.version_date)} - "
                    f"ID: {study.id}{is_latest_str}"
                )

            if len(studies) < 2 and not full:
                console.print(
                    "\n[yellow]Only one version found. No diff to display.[/yellow]"
                )
                return

            # Compare adjacent versions
            for i in range(len(studies)):
                current_study = studies[i]

                if i == 0:
                    console.print(
                        f"\n[bold]Initial Version: "
                        f"{format_date(current_study.version_date)}[/bold]"
                    )
                    if full:
                        # Construct full document for display
                        full_doc = {
                            "protocolSection": get_section_dict(
                                current_study.protocolSection
                            ),
                            "resultsSection": get_section_dict(
                                current_study.resultsSection
                            ),
                            "derivedSection": get_section_dict(
                                current_study.derivedSection
                            ),
                            "documentSection": get_section_dict(
                                current_study.documentSection
                            ),
                            "annotationSection": get_section_dict(
                                current_study.annotationSection
                            ),
                        }
                        # Remove None values
                        full_doc = {
                            k: v for k, v in full_doc.items() if v is not None
                        }
                        print_diff(
                            orjson.dumps(
                                full_doc, option=orjson.OPT_INDENT_2
                            )
                            .decode("utf-8")
                            .splitlines()
                        )
                    continue

                prev_study = studies[i - 1]

                console.print(
                    f"\n[bold]Diff: {format_date(prev_study.version_date)} -> "
                    f"{format_date(current_study.version_date)}[/bold]"
                )

                # Compare sections
                sections = [
                    ("protocolSection", "Protocol Section"),
                    ("resultsSection", "Results Section"),
                    ("derivedSection", "Derived Section"),
                    ("documentSection", "Document Section"),
                    ("annotationSection", "Annotation Section"),
                ]

                changes_found = False
                for field_name, display_name in sections:
                    prev_section = get_section_dict(
                        getattr(prev_study, field_name)
                    )
                    curr_section = get_section_dict(
                        getattr(current_study, field_name)
                    )
                    
                    # Exclude version metadata fields before comparison
                    prev_section = exclude_version_fields(prev_section)
                    curr_section = exclude_version_fields(curr_section)

                    if prev_section != curr_section:
                        # Handle cases where one is None and other isn't
                        if prev_section is None and curr_section is None:
                            continue

                        console.print(
                            f"[bold underline]{display_name}[/bold underline]"
                        )

                        prev_content = prev_section if prev_section else {}
                        curr_content = curr_section if curr_section else {}

                        diff_lines = generate_diff(prev_content, curr_content)
                        print_diff(diff_lines)
                        changes_found = True

                if not changes_found:
                    console.print(
                        "[italic]No changes in tracked sections.[/italic]"
                    )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        raise typer.Exit(code=1)
