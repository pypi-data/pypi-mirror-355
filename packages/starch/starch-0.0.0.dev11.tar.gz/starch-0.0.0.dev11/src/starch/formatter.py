"""Formatter

This module provides the main comment-formatting utility class.
"""

# ─── import statements ────────────────────────────────────────────────── ✦✦ ──

# standard library imports
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# third-party imports
import click

from .config import Configuration, config

# local imports
from .constants import STARCH_CONFIG_FILEPATH, STARCH_LOG_FILEPATH, __package__, __version__

# ─── logger setup ─────────────────────────────────────────────────────── ✦✦ ──

logging.basicConfig(filename=STARCH_LOG_FILEPATH, level=logging.INFO)
logger = logging.getLogger(__package__)


# ─── supported languages ──────────────────────────────────────────────── ✦✦ ──

SUPPORTED_EXTENSIONS = {
    # C/cpp
    "cpp": "cpp", "cxx": "cpp", "cc": "cpp", "c": "cpp",
    "h": "cpp", "hpp": "cpp", "hxx": "cpp",
    # Python
    "py": "python",
    # Rust
    "rs": "rust",
    # Swift
    "swift": "swift",
    # Haskell
    "hs": "haskell"
}


# ─── API ──────────────────────────────────────────────────────────────── ✦✦ ──

class CommentFormatter:
    _config: Configuration = config
   
    @classmethod
    def _get_config(
            cls, config_file: Path = STARCH_CONFIG_FILEPATH
    ) -> Configuration:
        """Get or initialize the configuration singleton."""
        if cls._config is None:
            try:
                # For singleton, create without parameters first
                cls._config = config
                
                # If a specific config file is requested, update the filepath
                if isinstance(cls._config, Configuration): 
                    cls._config.config_filepath = config_file
                    cls._config.load_config()
                    
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                raise
        elif config_file is not None and cls._config.config_filepath != config_file:
            # Handle case where different config file is requested
            cls._config.config_filepath = config_file
            cls._config.load_config()
            
        return cls._config

    @staticmethod
    def _default_options() -> Dict[str, Dict[str, Union[str, int]]]:
        """Return default configuration options."""
        return {
            "cpp": {
                "length": 80,
                "prefix": "// ─── ",
                "suffix": " ✦ ─"
            },
            "haskell": {
                "length": 80,
                "prefix": "-- ─── ",
                "suffix": " ✦ ─"
            },
            "python": {
                "length": 79,
                "prefix": "# ─── ",
                "suffix": " ✦ ─"
            },
            "rust": {
                "length": 80,
                "prefix": "// ─── ",
                "suffix": " ✦ ─"
            },
            "swift": {
                "length": 80,
                "prefix": "// ─── ",
                "suffix": " ✦ ─"
            }
        }
    
    @staticmethod
    def format_file(file_path: Path, lang: Optional[str] = None) -> bool:
        """Format a single file. Returns True if file was modified."""
        
        # Validate file exists first
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get configuration
        config = CommentFormatter._get_config()
        
        # Determine language from extension if not provided
        if lang is None:
            ext = file_path.suffix.lstrip(".").lower()
            lang = SUPPORTED_EXTENSIONS.get(ext)
            
            if lang is None:
                raise ValueError(f"File extension '.{ext}' is not supported.")

        # Validate language is supported
        if lang not in config.options:
            raise ValueError(f"Unsupported language: {lang}")

        updated_lines = []
        modified = False

        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    processed_line = CommentFormatter._process_line(line, lang, config)
                    updated_lines.append(processed_line)
                    if processed_line != line:
                        modified = True

            if modified:
                with file_path.open("w", encoding="utf-8") as f:
                    f.writelines(updated_lines)
                    
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

        return modified

    @staticmethod
    def check_file_needs_formatting(file_path: Path, lang: Optional[str] = None) -> bool:
        """Check if a file needs formatting without modifying it."""
        
        # Validate file exists first
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get configuration
        config = CommentFormatter._get_config()
        
        # Determine language from extension if not provided
        if lang is None:
            ext = file_path.suffix.lstrip(".").lower()
            lang = SUPPORTED_EXTENSIONS.get(ext)
            
            if lang is None:
                raise ValueError(f"File extension '.{ext}' is not supported.")

        # Validate language is supported
        if lang not in config.options:
            raise ValueError(f"Unsupported language: {lang}")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    processed_line = CommentFormatter._process_line(line, lang, config)
                    if processed_line != line:
                        return True
                        
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")
            raise

        return False

    @staticmethod
    def _process_line(line: str, lang: str, config: Configuration) -> str:
        """Process a single line, formatting starch comments."""

        # Define comment patterns for each language
        comment_patterns = {
            "python": r"^(\s*)# :(.*)$",
            "haskell": r"^(\s*)-- :(.*)$",
            "rust": r"^(\s*)// :(.*)$",
            "cpp": r"^(\s*)// :(.*)$",
            "swift": r"^(\s*)// :(.*)$",
        }

        if lang not in comment_patterns:
            raise NotImplementedError(f"Language '{lang}' is not yet supported.")

        match = re.match(comment_patterns[lang], line)
        if not match:
            return line

        indent, comment = match.groups()
        comment = comment.strip()
        
        # Access configuration using the options property
        lang_config = config.options.get(lang)
        if not lang_config:
            raise ValueError(f"No configuration found for language: {lang}")

        prefix = lang_config["prefix"]
        
        # Only add suffix for top-level comments (no indentation)
        if indent == "":
            suffix = lang_config["suffix"]
        else:
            suffix = ""

        # Calculate the maximum length for the comment text
        max_comment_length = (
            int(lang_config["length"])
            - len(str(prefix))
            - len(str(suffix))
            - len(str(indent))  # Account for indentation in total length
        )
        
        # Ensure we have at least some space for the comment
        if max_comment_length <= 0:
            logger.warning(f"Comment length too restrictive for language {lang}")
            max_comment_length = 10  # Minimum fallback
        
        # Trim comment to fit and calculate padding
        trimmed_comment = comment[:max_comment_length] if comment else ""
        
        # Calculate padding needed to reach the desired length
        # Format: indent + prefix + comment + padding + suffix
        current_length = len(indent) + len(str(prefix)) + len(str(trimmed_comment)) + len(str(suffix))
        target_length = lang_config["length"]
        padding_length = max(0, int(target_length) - int(current_length))
        
        # Create the padded comment line
        if trimmed_comment:
            # If there's a comment, add a space before padding
            padded_comment = f"{trimmed_comment} {'─' * max(0, padding_length - 1)}"
        else:
            # If no comment, just use padding
            padded_comment = "─" * padding_length

        return f"{indent}{prefix}{padded_comment}{suffix}\n"

    @staticmethod
    def get_source_files(
        path: Path,
        ignore_patterns: List[str],
        extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """Get source files in a directory recursively.

        Get all supported source files in a directory recursively,
        respecting ignore patterns.
        """
        if extensions is None:
            extensions = list(SUPPORTED_EXTENSIONS.keys())
        
        source_files = []
        ignore_set = set(ignore_patterns)

        def should_ignore(file_path: Path) -> bool:
            """Check if a path should be ignored."""
            path_str = str(file_path)
            path_name = file_path.name

            # Always ignore hidden directories and files (starting with .)
            if any(part.startswith('.') and part != '.' and part != '..' for part in file_path.parts):
                return True

            # Check if any part of the path matches ignore patterns
            for pattern in ignore_set:
                if pattern in path_str or pattern == path_name:
                    return True
                # Check if any parent directory matches the pattern
                for parent in file_path.parents:
                    if parent.name == pattern:
                        return True
            return False

        if path.is_file():
            ext = path.suffix.lstrip(".").lower()
            if ext in extensions and not should_ignore(path):
                source_files.append(path)
        elif path.is_dir():
            for ext in extensions:
                for source_file in path.rglob(f"*.{ext}"):
                    if not should_ignore(source_file):
                        source_files.append(source_file)

        return sorted(source_files)


# ─── command-line interface ───────────────────────────────────────────── ✦✦ ──

# Common options that can be shared across commands
def common_options(f):
    """Decorator to add common options to commands."""
    f = click.option(
        "--config-file",
        type=click.Path(path_type=Path),
        default=STARCH_CONFIG_FILEPATH,
        help="Path to configuration file",
    )(f)
    f = click.option(
        "--verbose", 
        "-v", 
        is_flag=True, 
        help="Show verbose output"
    )(f)
    return f

@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    help="Show starch's version string."
)
@click.pass_context
def cli(ctx, version):
    """Starch - A comment formatter for source code files.
    
    Format decorated comment lines in source files with support for multiple
    programming languages.
    """
    if version:
        click.echo(f"starch, v{__version__}")
        return
        
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument(
    "src", 
    nargs=-1, 
    type=click.Path(exists=True, path_type=Path),
    required=True
)
@click.option(
    "--lang",
    "-l",
    help="Language of the source files (auto-detected if not specified)",
)
@click.option(
    "--ignore",
    "-i",
    multiple=True,
    help="Directory or file patterns to ignore (can be used multiple times)",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be formatted without making changes",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check if files would be reformatted. Exit with code 1 if they would.",
)
@common_options
def format(src, lang, ignore, dry_run, check, verbose, config_file):
    """Format source code files.
    
    Format decorated comment lines in source files. Supports multiple files
    and directories.

    \b
    Examples:
        starch format .                             # Format all files in current directory
        starch format src/ tests/                   # Format multiple directories
        starch format file.py another.rs            # Format specific files
        starch format . --lang python               # Format only Python files
        starch format . --ignore __pycache__        # Ignore specific patterns
        starch format . --dry-run                   # Preview changes
        starch format . --check                     # Check if formatting needed
    """
    
    # Set up ignore patterns
    ignore_patterns = list(ignore) if ignore else [
        "__pycache__",  # Python
        "node_modules",  # JavaScript/TypeScript
        "build",  # Generic build
        "dist",  # Generic distribution
        ".git",  # Git
        "target",  # Rust
        ".build",  # Swift build
    ]
    
    try:
        # Load configuration
        config = CommentFormatter._get_config(config_file)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)
    
    # Collect all files to process
    all_files = []
    for path in src:
        if path.is_file():
            ext = path.suffix.lstrip(".").lower()
            if ext in SUPPORTED_EXTENSIONS:
                all_files.append(path)
        else:
            # Get files from directory
            extensions = None
            if lang:
                extensions = [ext for ext, language in SUPPORTED_EXTENSIONS.items() if language == lang]
            
            directory_files = CommentFormatter.get_source_files(
                path, ignore_patterns, extensions
            )
            all_files.extend(directory_files)
    
    if not all_files:
        if lang:
            click.echo(f"No {lang} files found to process.")
        else:
            click.echo("No supported files found.")
        return
    
    # Process files
    modified_files = []
    would_modify_files = []
    error_files = []
    
    for file_path in all_files:
        try:
            file_lang = lang or SUPPORTED_EXTENSIONS[file_path.suffix.lstrip(".").lower()]
            
            if dry_run or check:
                # Use the same check method for consistency
                would_modify = CommentFormatter.check_file_needs_formatting(file_path, file_lang)
                if would_modify:
                    would_modify_files.append(file_path)
                    if dry_run:
                        click.echo(f"would reformat {file_path}")
                    elif verbose:
                        click.echo(f"would reformat {file_path}")
                elif verbose and not check:
                    click.echo(f"unchanged {file_path}")
            else:
                # Actually format the file
                was_modified = CommentFormatter.format_file(file_path, file_lang)
                if was_modified:
                    modified_files.append(file_path)
                    if verbose:
                        click.echo(f"reformatted {file_path}")
                elif verbose:
                    click.echo(f"unchanged {file_path}")
                    
        except Exception as e:
            error_files.append((file_path, str(e)))
            click.echo(f"error: cannot format {file_path}: {e}", err=True)
   
    # Summary output
    if check:
        if would_modify_files:
            click.echo(f"would reformat {len(would_modify_files)} files")
            sys.exit(1)  # Exit with error code if files would be changed
        else:
            if verbose:
                click.echo(f"checked {len(all_files)} files")
    elif dry_run:
        if would_modify_files:
            click.echo(f"would reformat {len(would_modify_files)} files")
        else:
            click.echo("no changes needed")
    else:
        # Actual formatting summary
        if error_files:
            click.echo(f"failed to format {len(error_files)} files", err=True)
            sys.exit(1)
        else:
            # Always show success message with total files processed
            click.echo(f"Formatted {len(all_files)} files.")
            if verbose and modified_files:
                click.echo(f"({len(modified_files)} files were modified)")


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command(name="show")
@common_options
def show_config(verbose, config_file):
    """Show the current configuration."""
    try:
        config = CommentFormatter._get_config(config_file)
        if not config.options:
            click.echo("No configuration found.")
            return
            
        click.echo(f"Configuration file: {config.config_filepath}")
        click.echo()
        for lang_name, settings in config.options.items():
            click.echo(f"{lang_name}:")
            for key, value in settings.items():
                if isinstance(value, str):
                    click.echo(f'  {key} = "{value}"')
                else:
                    click.echo(f"  {key} = {value}")
            click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command(name="path")
@common_options
def config_path(verbose, config_file):
    """Show the path to the configuration file."""
    try:
        config = CommentFormatter._get_config(config_file)
        click.echo(f"Configuration file: {config.config_filepath}")
        click.echo(f"Exists: {'Yes' if config.config_filepath.exists() else 'No'}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command(name="get")
@click.argument("key", metavar="LANG.SETTING")
@common_options
def get_config(key, verbose, config_file):
    """Get a configuration value.
    
    \b
    Examples:
        starch config get python.length
        starch config get rust.prefix
    """
    try:
        if "." not in key:
            click.echo("Error: Config key must be in format LANGUAGE.SETTING", err=True)
            sys.exit(1)
            
        language, setting = key.split(".", 1)
        config = CommentFormatter._get_config(config_file)
        
        if language not in config.options:
            click.echo(f"Error: Language '{language}' not found.", err=True)
            click.echo(f"Available: {', '.join(config.options.keys())}")
            sys.exit(1)
            
        if setting not in config.options[language]:
            click.echo(f"Error: Setting '{setting}' not found for {language}.", err=True)
            click.echo(f"Available: {', '.join(config.options[language].keys())}")
            sys.exit(1)
            
        value = config.options[language][setting]
        if isinstance(value, str):
            click.echo(f'{key} = "{value}"')
        else:
            click.echo(f"{key} = {value}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command(name="set")
@click.argument("assignment", metavar="LANG.SETTING=VALUE")
@common_options
def set_config(assignment, verbose, config_file):
    """Set a configuration value.
    
    \b
    Examples:
        starch config set python.length=80
        starch config set rust.prefix="// --- "
    """
    try:
        if "=" not in assignment:
            click.echo("Error: Config setting must be in format LANGUAGE.SETTING=VALUE", err=True)
            sys.exit(1)
            
        key_part, value = assignment.split("=", 1)
        if "." not in key_part:
            click.echo("Error: Config key must be in format LANGUAGE.SETTING=VALUE", err=True)
            sys.exit(1)
            
        language, setting = key_part.split(".", 1)
        config = CommentFormatter._get_config(config_file)
        
        if language not in config.options:
            click.echo(f"Error: Language '{language}' not found.", err=True)
            sys.exit(1)
            
        if setting not in config.options[language]:
            click.echo(f"Error: Setting '{setting}' not found for {language}.", err=True)
            sys.exit(1)
            
        # Type conversion
        current_value = config.options[language][setting]
        try:
            if isinstance(current_value, int):
                new_value = int(value)
            elif isinstance(current_value, bool):
                new_value = value.lower() in ("true", "1", "yes", "on")
            else:
                new_value = value
        except ValueError:
            click.echo(f"Error: Cannot convert '{value}' to expected type.", err=True)
            sys.exit(1)
            
        config.options[language][setting] = new_value
        config.save_config()
        
        if isinstance(new_value, str):
            click.echo(f'Set {key_part} = "{new_value}"')
        else:
            click.echo(f"Set {key_part} = {new_value}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command(name="reset")
@click.argument("language")
@common_options
def reset_config(language, verbose, config_file):
    """Reset configuration for a language or all languages.
    
    Use 'all' to reset all language configurations.
    
    \b
    Examples:
        starch config reset python
        starch config reset all
    """
    try:
        config = CommentFormatter._get_config(config_file)
        defaults = CommentFormatter._default_options()
        
        if language == "all":
            config.options = {lang: defaults[lang].copy() for lang in defaults}
            config.save_config()
            click.echo("Reset all language configurations to defaults.")
        else:
            if language not in defaults:
                click.echo(f"Error: Language '{language}' not supported.", err=True)
                click.echo(f"Available: {', '.join(defaults.keys())}")
                sys.exit(1)
                
            config.options[language] = defaults[language].copy()
            config.save_config()
            click.echo(f"Reset {language} configuration to defaults.")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
