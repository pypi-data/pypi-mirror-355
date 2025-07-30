# src/codebrief/tools/tree_generator.py

"""Directory Tree Generation Utilities.

This module provides functions to generate a textual or Rich-enhanced representation
of a directory's structure. It supports excluding specified files and directories
and can output the tree to the console or a file.

Core functionalities:
- Recursive traversal of directories.
- Filtering of items based on .llmignore files, CLI arguments, core system
  exclusions, and a default set of common development artifacts.
- Generation of plain text tree for file output.
- Generation of a Rich `Tree` object for styled console output.
"""

from pathlib import Path
from typing import Any, Optional

import pathspec  # For type hinting the llmignore_spec
import typer
from rich.console import Console
from rich.tree import Tree as RichTree

# Import the ignore handler utility
from ..utils import ignore_handler  # Assuming utils is in the parent package

console = Console()

# DEFAULT_EXCLUDED_ITEMS: This set can act as a fallback or for items
# not typically in .llmignore but that this tool should generally skip
# if no other rules apply. Its role is reduced now that .llmignore is primary.
# It's checked if ignore_handler.is_path_ignored returns False and no specific
# llmignore file was found. Consider removing or significantly reducing this list
# if .llmignore + CORE_SYSTEM_EXCLUSIONS in ignore_handler is sufficient.
DEFAULT_EXCLUDED_ITEMS_TOOL_SPECIFIC: set[str] = {
    # Items that might be specific to tree generation context,
    # e.g., the output file name if not handled by other means.
    # For now, let's keep the original list and see how it plays out.
    # Version Control (already in ignore_handler.CORE_SYSTEM_EXCLUSIONS but good for direct name check)
    ".git",
    ".hg",
    ".svn",
    # Python specific
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    ".env",
    "pip-wheel-metadata",
    "*.egg-info",
    # Node.js specific
    "node_modules",
    "package-lock.json",
    "yarn.lock",
    # IDE specific
    ".vscode",
    ".idea",
    "*.iml",
    # Build artifacts & Distribution
    "dist",
    "build",
    "target",
    "out",
    # OS specific
    ".DS_Store",
    "Thumbs.db",
    # Logs and temp files (better handled by .llmignore or CLI)
    # "*.log", "*.tmp", "*.swp", # Commenting out, as .llmignore is better for patterns
    # "project_tree.txt", # This should be handled dynamically if it's the output file
}


def _should_skip_this_item_name_fallback(
    item_name: str, fallback_exclusions: set[str]
) -> bool:
    """Fallback check against a simple set of names/basic patterns.
    Used if .llmignore spec doesn't exist or doesn't cover everything.
    """
    if item_name in fallback_exclusions:  # Exact name match
        return True
    return any(
        Path(item_name).match(pattern) for pattern in fallback_exclusions
    )  # Glob match like *.log


def _should_show_path(
    path: Path,
    root_dir_for_ignores: Path,
    llmignore_spec: Optional[pathspec.PathSpec],
    cli_ignores: Optional[list[str]],
    config_global_excludes: Optional[list[str]],  # <--- NEW PARAMETER
    tool_specific_fallback_exclusions: set[str],
) -> bool:
    """Determine if a path should be shown in the tree, considering all ignore sources."""
    is_ignored_by_main_rules = ignore_handler.is_path_ignored(
        path_to_check=path,
        root_dir=root_dir_for_ignores,
        ignore_spec=llmignore_spec,
        cli_ignore_patterns=cli_ignores,  # Passed to ignore_handler
        config_exclude_patterns=config_global_excludes,
    )

    if is_ignored_by_main_rules:
        return False

    # Fallback applies if no .llmignore was found AND no global config excludes were defined
    # (as config excludes also represent a form of explicit project-level ignore rules)
    if (
        llmignore_spec is None
        and not config_global_excludes
        and _should_skip_this_item_name_fallback(
            path.name, tool_specific_fallback_exclusions
        )
    ):
        return False

    return True


def _generate_tree_lines_recursive(
    current_dir: Path,
    root_dir_for_ignores: Path,
    llmignore_spec: Optional[pathspec.PathSpec],
    cli_ignores: Optional[list[str]],
    config_global_excludes: Optional[list[str]],
    tool_specific_fallback_exclusions: set[str],
    prefix: str = "",
    is_last_at_level: bool = True,
) -> list[str]:
    lines: list[str] = []

    if is_last_at_level:
        lines.append(f"{current_dir.name}/")

    try:
        all_children_sorted = sorted(
            current_dir.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
        )
    except (PermissionError, FileNotFoundError) as e:
        error_msg = f"(Permission Denied for {current_dir.name}/)"
        if isinstance(e, FileNotFoundError):
            error_msg = f"(Directory not found: {current_dir.name}/)"
        lines.append(f"{prefix}└── [dim italic]{error_msg}[/dim italic]")
        return lines

    displayable_children: list[Path] = []
    child_to_processing_results: dict[str, Any] = {}

    for child_path in all_children_sorted:
        is_child_itself_displayable_by_rule = _should_show_path(
            child_path,
            root_dir_for_ignores,
            llmignore_spec,
            cli_ignores,
            config_global_excludes,
            tool_specific_fallback_exclusions,
        )

        generated_grandchild_lines = []
        if child_path.is_dir():
            generated_grandchild_lines = _generate_tree_lines_recursive(
                current_dir=child_path,
                root_dir_for_ignores=root_dir_for_ignores,
                llmignore_spec=llmignore_spec,
                cli_ignores=cli_ignores,
                config_global_excludes=config_global_excludes,
                tool_specific_fallback_exclusions=tool_specific_fallback_exclusions,
                prefix="",
                is_last_at_level=False,
            )

        should_render_this_entry = is_child_itself_displayable_by_rule or (
            child_path.is_dir() and generated_grandchild_lines
        )

        child_to_processing_results[child_path.name] = {
            "should_render": should_render_this_entry,
            "grandchild_lines": generated_grandchild_lines,
        }
        if should_render_this_entry:
            displayable_children.append(child_path)

    num_displayable_entries = len(displayable_children)
    rendered_entry_count = 0

    for (
        child_path
    ) in displayable_children:  # Iterate only over those that will be displayed
        processing_result = child_to_processing_results[child_path.name]
        # is_child_displayed was already confirmed (it's in displayable_children)
        generated_grandchild_lines = processing_result["grandchild_lines"]

        rendered_entry_count += 1
        connector = (
            "└── " if rendered_entry_count == num_displayable_entries else "├── "
        )
        line_prefix_for_child = prefix + connector

        lines.append(
            f"{line_prefix_for_child}{child_path.name}{'/' if child_path.is_dir() else ''}"
        )

        if child_path.is_dir() and generated_grandchild_lines:
            child_contents_prefix_extension = "    " if connector == "└── " else "│   "
            for grandchild_line in generated_grandchild_lines:
                lines.append(prefix + child_contents_prefix_extension + grandchild_line)
    return lines


def _add_nodes_to_rich_tree_recursive(
    rich_tree_node: RichTree,
    current_path_obj: Path,
    root_dir_for_ignores: Path,
    llmignore_spec: Optional[pathspec.PathSpec],
    cli_ignores: Optional[list[str]],
    config_global_excludes: Optional[list[str]],
    tool_specific_fallback_exclusions: set[str],
) -> None:
    try:
        all_children_sorted = sorted(
            current_path_obj.iterdir(),
            key=lambda x: (x.is_file(), x.name.lower()),
        )
    except (PermissionError, FileNotFoundError) as e:
        error_msg = "(Permission Denied)"
        if isinstance(e, FileNotFoundError):
            error_msg = f"(Directory {current_path_obj.name} not found)"
        rich_tree_node.add(f"[dim italic]{error_msg}[/dim italic]")
        return

    for child_path in all_children_sorted:
        if _should_show_path(  # Use the unified helper
            child_path,
            root_dir_for_ignores,
            llmignore_spec,
            cli_ignores,
            config_global_excludes,
            tool_specific_fallback_exclusions,
        ):
            if child_path.is_dir():
                branch_label = f"📁 {child_path.name}"
                branch = rich_tree_node.add(branch_label, guide_style="blue")
                _add_nodes_to_rich_tree_recursive(
                    rich_tree_node=branch,
                    current_path_obj=child_path,
                    root_dir_for_ignores=root_dir_for_ignores,
                    llmignore_spec=llmignore_spec,
                    cli_ignores=cli_ignores,
                    config_global_excludes=config_global_excludes,
                    tool_specific_fallback_exclusions=tool_specific_fallback_exclusions,
                )
            else:
                file_label = f"📄 {child_path.name}"
                rich_tree_node.add(file_label)


def generate_and_output_tree(
    root_dir: Path,
    output_file_path: Optional[Path] = None,
    ignore_list: Optional[list[str]] = None,
    config_global_excludes: Optional[list[str]] = None,  # <--- NEW PARAMETER
) -> Optional[str]:
    """Generate and output tree structure.

    Args:
        root_dir: Root directory to generate tree for.
        output_file_path: Optional path to save the tree. If None, returns string for console.
        ignore_list: List of patterns to ignore.
        config_global_excludes: Global exclusion patterns from config.

    Returns:
        String representation of the tree if no output file specified, None otherwise.
    """
    if not root_dir.is_dir():
        console.print(
            f"[bold red]Error: Root directory '{root_dir}' not found or is not a directory.[/bold red]"
        )
        raise typer.Exit(code=1)

    llmignore_spec = ignore_handler.load_ignore_patterns(root_dir)
    # Simplified console message logic for brevity, can be restored from your version
    if (
        llmignore_spec
        and output_file_path
        and (root_dir / ignore_handler.LLMIGNORE_FILENAME).exists()
    ):
        console.print(
            f"[dim]Using .llmignore patterns from '{root_dir / ignore_handler.LLMIGNORE_FILENAME}'[/dim]"
        )
    elif not llmignore_spec and output_file_path:
        console.print(
            "[dim]No .llmignore file, or it's empty. Using fallback exclusions if applicable.[/dim]"
        )

    effective_cli_ignores = list(ignore_list) if ignore_list else []
    if output_file_path:
        abs_output_file = output_file_path.resolve()
        if (
            abs_output_file.is_relative_to(root_dir.resolve())
            and abs_output_file.name not in effective_cli_ignores
        ):
            effective_cli_ignores.append(abs_output_file.name)
            # Re-add this console print if desired
            # console.print(f"[dim]Output file '{abs_output_file.name}' will be dynamically ignored for this run.[/dim]")

    current_tool_specific_exclusions = DEFAULT_EXCLUDED_ITEMS_TOOL_SPECIFIC.copy()

    # Create Rich tree for both file output and console display
    rich_tree_root_label = f"📁 [link file://{root_dir.resolve()}]{root_dir.name}"
    rich_tree_root = RichTree(
        rich_tree_root_label,
        guide_style="bold bright_blue",
    )
    _add_nodes_to_rich_tree_recursive(
        rich_tree_node=rich_tree_root,
        current_path_obj=root_dir,
        root_dir_for_ignores=root_dir,
        llmignore_spec=llmignore_spec,
        cli_ignores=effective_cli_ignores,
        config_global_excludes=config_global_excludes,
        tool_specific_fallback_exclusions=current_tool_specific_exclusions,
    )

    if output_file_path:
        # Render Rich tree to string for file output
        from io import StringIO

        from rich.console import Console as RichConsole

        string_buffer = StringIO()
        file_console = RichConsole(file=string_buffer, width=120, legacy_windows=False)
        file_console.print(rich_tree_root)
        rich_output = string_buffer.getvalue()

        try:
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            with output_file_path.open(mode="w", encoding="utf-8") as f:
                f.write(rich_output)
            console.print(
                f"Directory tree saved to [cyan]{output_file_path.resolve()}[/cyan]"
            )
        except OSError as e:
            console.print(
                f"[bold red]Error writing to output file '{output_file_path}': {e}[/bold red]"
            )
            raise typer.Exit(code=1) from e
        return None
    else:
        # Return the string representation for console output or clipboard
        from io import StringIO

        from rich.console import Console as RichConsole

        string_buffer = StringIO()
        console_for_capture = RichConsole(
            file=string_buffer, width=120, legacy_windows=False
        )
        console_for_capture.print(rich_tree_root)
        return string_buffer.getvalue()
