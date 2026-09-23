import json
import difflib
from rich.console import Console

console = Console()

def generate_diff(old_content: dict, new_content: dict, context_lines: int = 3):
    """Generate a unified diff between two dictionaries."""
    
    # Dump to pretty-printed JSON strings
    old_str = json.dumps(old_content, sort_keys=True, indent=2, default=str)
    new_str = json.dumps(new_content, sort_keys=True, indent=2, default=str)
    
    old_lines = old_str.splitlines()
    new_lines = new_str.splitlines()
    
    return list(difflib.unified_diff(
        old_lines, 
        new_lines, 
        fromfile='Previous Version', 
        tofile='New Version',
        n=context_lines,
        lineterm=""
    ))

def print_diff(diff_lines):
    """Print the diff with syntax highlighting."""
    if not diff_lines:
        return

    # Join lines and print using rich for coloring
    for line in diff_lines:
        if line.startswith('---') or line.startswith('+++'):
            console.print(line, style="bold")
        elif line.startswith('@@'):
            console.print(line, style="cyan")
        elif line.startswith('+'):
            console.print(line, style="green")
        elif line.startswith('-'):
            console.print(line, style="red")
        else:
            console.print(line)

def run_db_diff():
    # Data provided by user (simulated DB records)
    # Format: id, nct_id, version_date, content_hash, is_latest, protocolSection, resultsSection, derivedSection, ...
    
    # We will focus on comparing the JSON content of the versions provided.
    # The user provided 4 records. Let's parse them.
    # Note: The input is a bit messy (copy-paste from DB output), so I'll manually reconstruct the JSON objects 
    # based on the provided strings to compare them.
    
    # Record 1 (ID 337063) - 2020-11-03 (Oldest in this set based on IDs/order provided? No, let's look at version_date)
    # Wait, all version_dates are "2020-11-03 00:00:00+00". This is interesting.
    # The IDs are: 337063, 580651, 1555994, 1868208
    # Let's assume ID order is chronological order of insertion.
    
    # I'll extract the 'derivedSection' specifically since that seems to have the 'versionHolder' which differs in the text.
    # Record 1 (337063): versionHolder = "2025-12-23"
    # Record 2 (580651): versionHolder = "2025-12-26"
    # Record 3 (1555994): versionHolder = "2025-12-29"
    # Record 4 (1868208): versionHolder = "2025-12-30"
    
    # Let's verify this hypothesis by extracting just the JSON parts provided.
    
    records = [
        {
            "id": 337063,
            "derivedSection": {"miscInfoModule": {"versionHolder": "2025-12-23", "removedCountries": None, "submissionTracking": None}, "conditionBrowseModule": {"meshes": [{"id": "D014947", "term": "Wounds and Injuries"}], "ancestors": None, "browseLeaves": None, "browseBranches": None}, "interventionBrowseModule": None}
        },
        {
            "id": 580651,
            "derivedSection": {"miscInfoModule": {"versionHolder": "2025-12-26", "removedCountries": None, "submissionTracking": None}, "conditionBrowseModule": {"meshes": [{"id": "D014947", "term": "Wounds and Injuries"}], "ancestors": None, "browseLeaves": None, "browseBranches": None}, "interventionBrowseModule": None}
        },
        {
            "id": 1555994,
            "derivedSection": {"miscInfoModule": {"versionHolder": "2025-12-29", "removedCountries": None, "submissionTracking": None}, "conditionBrowseModule": {"meshes": [{"id": "D014947", "term": "Wounds and Injuries"}], "ancestors": None, "browseLeaves": None, "browseBranches": None}, "interventionBrowseModule": None}
        },
        {
            "id": 1868208,
            "derivedSection": {"miscInfoModule": {"versionHolder": "2025-12-30", "removedCountries": None, "submissionTracking": None}, "conditionBrowseModule": {"meshes": [{"id": "D014947", "term": "Wounds and Injuries"}], "ancestors": None, "browseLeaves": None, "browseBranches": None}, "interventionBrowseModule": None}
        }
    ]
    
    # Also let's check protocolSection for Record 1 vs Record 2 to see if anything else changed.
    # The user provided full strings, I will try to diff the Derived Section first as it clearly changed.
    
    print("Comparing Derived Sections:")
    for i in range(len(records) - 1):
        prev = records[i]
        curr = records[i+1]
        print(f"\nDiff ID {prev['id']} -> {curr['id']}")
        diff = generate_diff(prev['derivedSection'], curr['derivedSection'])
        print_diff(diff)

if __name__ == "__main__":
    run_db_diff()

