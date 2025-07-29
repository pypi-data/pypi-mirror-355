#!/usr/bin/env python3

"""
CLI tool to add new patterns to settings in home directory (~/.jgt/settings.json)
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Any

# Add the jgtutils directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jgtcommon


def load_home_settings() -> Dict[str, Any]:
    """Load settings from home directory."""
    home_settings_path = os.path.join(os.path.expanduser('~'), '.jgt', 'settings.json')
    
    if os.path.exists(home_settings_path):
        with open(home_settings_path, 'r') as f:
            return json.load(f)
    else:
        # Create empty settings structure
        return {
            "patterns": {}
        }


def save_home_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to home directory."""
    home_settings_dir = os.path.join(os.path.expanduser('~'), '.jgt')
    home_settings_path = os.path.join(home_settings_dir, 'settings.json')
    
    # Create directory if it doesn't exist
    os.makedirs(home_settings_dir, exist_ok=True)
    
    try:
        with open(home_settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def add_pattern_to_settings(pattern_name: str, columns: List[str], force: bool = False) -> bool:
    """Add a new pattern to home settings."""
    settings = load_home_settings()
    
    # Initialize patterns section if it doesn't exist
    if "patterns" not in settings:
        settings["patterns"] = {}
    
    # Check if pattern already exists
    if pattern_name in settings["patterns"] and not force:
        print(f"Pattern '{pattern_name}' already exists. Use --force to overwrite.")
        return False
    
    # Add the pattern
    settings["patterns"][pattern_name] = {
        "columns": columns
    }
    
    # Save settings
    if save_home_settings(settings):
        if pattern_name in settings["patterns"] and not force:
            print(f"Updated pattern '{pattern_name}' with columns: {columns}")
        else:
            print(f"Added pattern '{pattern_name}' with columns: {columns}")
        return True
    else:
        return False


def list_patterns() -> None:
    """List all patterns in home settings."""
    settings = load_home_settings()
    
    if "patterns" not in settings or not settings["patterns"]:
        print("No patterns found in home settings.")
        return
    
    print("Patterns in home settings:")
    print("-" * 40)
    for pattern_name, pattern_data in settings["patterns"].items():
        columns = pattern_data.get("columns", [])
        print(f"{pattern_name}: {', '.join(columns)}")


def remove_pattern_from_settings(pattern_name: str) -> bool:
    """Remove a pattern from home settings."""
    settings = load_home_settings()
    
    if "patterns" not in settings or pattern_name not in settings["patterns"]:
        print(f"Pattern '{pattern_name}' not found in home settings.")
        return False
    
    del settings["patterns"][pattern_name]
    
    if save_home_settings(settings):
        print(f"Removed pattern '{pattern_name}' from home settings.")
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add, list, or remove patterns in home settings (~/.jgt/settings.json)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a new pattern
  python add_pattern_to_home_settings.py --add-pattern mypattern --columns col1 col2 col3
  
  # List all patterns
  python add_pattern_to_home_settings.py --list-patterns
  
  # Remove a pattern
  python add_pattern_to_home_settings.py --remove-pattern mypattern
  
  # Force overwrite existing pattern
  python add_pattern_to_home_settings.py --add-pattern mypattern --columns newcol1 newcol2 --force
        """
    )
    
    # Action group (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--add-pattern", 
        type=str,
        help="Name of the pattern to add"
    )
    action_group.add_argument(
        "--list-patterns",
        action="store_true",
        help="List all patterns in home settings"
    )
    action_group.add_argument(
        "--remove-pattern",
        type=str,
        help="Name of the pattern to remove"
    )
    
    # Additional arguments for adding patterns
    parser.add_argument(
        "--columns",
        nargs="+",
        help="List of columns for the pattern (required when adding pattern)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite if pattern already exists"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.add_pattern and not args.columns:
        parser.error("--columns is required when adding a pattern")
    
    # Execute actions
    if args.add_pattern:
        success = add_pattern_to_settings(args.add_pattern, args.columns, args.force)
        sys.exit(0 if success else 1)
    elif args.list_patterns:
        list_patterns()
    elif args.remove_pattern:
        success = remove_pattern_from_settings(args.remove_pattern)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 