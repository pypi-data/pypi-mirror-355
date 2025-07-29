"""
Command line interface for mdump
"""

import os
import sys
from pathlib import Path
from typing import Optional
import click
import pyperclip

from .core import ProjectDumper


@click.command()
@click.argument('path', default='.', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path (default: stdout)'
)
@click.option(
    '--clipboard', '-c',
    is_flag=True,
    help='Copy output to clipboard'
)
@click.option(
    '--exclude-dirs',
    help='Comma-separated list of directories to exclude'
)
@click.option(
    '--exclude-files',
    help='Comma-separated list of files to exclude'
)
@click.option(
    '--exclude-extensions',
    help='Comma-separated list of file extensions to exclude (e.g., .pyc,.log)'
)
@click.option(
    '--include-gitignore',
    is_flag=True,
    help="Include .gitignore and other config files in output"
)
@click.option(
    '--max-file-size',
    type=int,
    default=1024*1024,
    help='Maximum file size to include in bytes (default: 1MB)'
)
@click.version_option()
def main(
    path: str,
    output: Optional[str],
    clipboard: bool,
    exclude_dirs: Optional[str],
    exclude_files: Optional[str], 
    exclude_extensions: Optional[str],
    include_gitignore: bool,
    max_file_size: int
):
    """
    Generate a Markdown dump of project structure and file contents.
    
    PATH: Target directory to dump (default: current directory)
    """
    try:
        # Parse exclusion lists
        exclude_dirs_list = []
        if exclude_dirs:
            exclude_dirs_list = [d.strip() for d in exclude_dirs.split(',')]
        
        exclude_files_list = []
        if exclude_files:
            exclude_files_list = [f.strip() for f in exclude_files.split(',')]
            
        exclude_extensions_list = []
        if exclude_extensions:
            exclude_extensions_list = [
                ext.strip() if ext.strip().startswith('.') else f'.{ext.strip()}'
                for ext in exclude_extensions.split(',')
            ]
        
        # Create dumper
        dumper = ProjectDumper(
            target_path=path,
            exclude_dirs=exclude_dirs_list,
            exclude_files=exclude_files_list,
            exclude_extensions=exclude_extensions_list,
            use_gitignore=not include_gitignore,
            exclude_defaults=not include_gitignore,
            max_file_size=max_file_size
        )
        
        # Generate dump
        click.echo("Generating project dump...", err=True)
        dump_content = dumper.generate_dump()
        
        # Output handling
        if output:
            # Write to file
            output_path = Path(output)
            output_path.write_text(dump_content, encoding='utf-8')
            click.echo(f"Dump saved to: {output_path}", err=True)
        else:
            # Print to stdout
            click.echo(dump_content)
        
        # Copy to clipboard if requested
        if clipboard:
            try:
                pyperclip.copy(dump_content)
                click.echo("Dump copied to clipboard!", err=True)
            except pyperclip.PyperclipException as e:
                click.echo(f"Warning: Could not copy to clipboard: {e}", err=True)
        
        click.echo("Done!", err=True)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
