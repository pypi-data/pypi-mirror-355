"""
Core functionality for mdump
"""

import os
import stat
from pathlib import Path
from typing import List, Set, Optional, Tuple
import fnmatch
import mimetypes
from git import Repo, InvalidGitRepositoryError
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


class ProjectDumper:
    """Main class for dumping project structure and contents"""
    
    def __init__(
        self,
        target_path: str = ".",
        exclude_dirs: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None,
        exclude_extensions: Optional[List[str]] = None,
        use_gitignore: bool = True,
        exclude_defaults: bool = True,
        max_file_size: int = 1024 * 1024,  # 1MB
    ):
        self.target_path = Path(target_path).resolve()
        self.exclude_dirs = set(exclude_dirs or [])
        self.exclude_files = set(exclude_files or [])
        self.exclude_extensions = set(exclude_extensions or [])
        self.use_gitignore = use_gitignore
        self.exclude_defaults = exclude_defaults
        self.max_file_size = max_file_size
        
        # Default exclusions (only if exclude_defaults is True)
        if self.exclude_defaults:
            self.exclude_dirs.update({
                '.git', '.svn', '.hg', '.bzr',
                '__pycache__', '.pytest_cache', '.tox',
                'node_modules', '.next', '.nuxt',
                'venv', '.venv', 'env', '.env',
                'dist', 'build', '.dist', '.build',
                '.idea', '.vscode', '.vs',
                'target', 'bin', 'obj',
            })
            
            self.exclude_extensions.update({
                '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
                '.exe', '.bin', '.o', '.a', '.lib',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
                '.log', '.tmp', '.temp', '.cache', '.swp', '.swo',
                '.lock',  # Lock files (package-lock.json, yarn.lock, Pipfile.lock, etc.)
            })
            
            # Default files to exclude (regardless of extension)
            self.exclude_files.update({
                '.gitignore', '.gitattributes', '.gitmodules',
                '.dockerignore', '.eslintignore', '.prettierignore',
                '.editorconfig', '.browserslistrc',
                'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
                'Pipfile.lock', 'poetry.lock', 'uv.lock',
                'Gemfile.lock', 'composer.lock', 'go.sum',
                'Cargo.lock', 'mix.lock', 'packages.lock.json',
                '.DS_Store', 'Thumbs.db', 'desktop.ini', 'LICENSE'
            })
        
        self.gitignore_spec = self._load_gitignore()
    
    def _load_gitignore(self) -> Optional[PathSpec]:
        """Load .gitignore patterns"""
        if not self.use_gitignore:
            return None
            
        gitignore_patterns = []
        
        # Look for .gitignore files from target directory up to root
        current_path = self.target_path
        while current_path != current_path.parent:
            gitignore_file = current_path / '.gitignore'
            if gitignore_file.exists():
                try:
                    with open(gitignore_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                gitignore_patterns.append(line)
                except Exception:
                    pass
            current_path = current_path.parent
        
        if gitignore_patterns:
            return PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)
        return None
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary"""
        try:
            # Check by extension first
            if file_path.suffix.lower() in self.exclude_extensions:
                return True
                
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and not mime_type.startswith('text/'):
                return True
            
            # Check file content for binary data
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\x00' in chunk:
                        return True
            except Exception:
                return True
                
            return False
        except Exception:
            return True
    
    def _should_exclude_path(self, path: Path, is_dir: bool = False) -> bool:
        """Check if path should be excluded"""
        # Check gitignore
        if self.gitignore_spec:
            relative_path = path.relative_to(self.target_path)
            if self.gitignore_spec.match_file(str(relative_path)):
                return True
        
        # Check explicit exclusions
        if is_dir and path.name in self.exclude_dirs:
            return True
            
        if not is_dir:
            if path.name in self.exclude_files:
                return True
            if path.suffix.lower() in self.exclude_extensions:
                return True
        
        return False
    
    def _generate_tree_structure(self, path: Path, prefix: str = "", is_last: bool = True) -> List[str]:
        """Generate tree-like structure representation"""
        lines = []
        
        if path == self.target_path:
            lines.append(f"{path.name}/")
            prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            if path.is_dir():
                lines.append(f"{prefix}{connector}{path.name}/")
            else:
                lines.append(f"{prefix}{connector}{path.name}")
        
        if path.is_dir() and not self._should_exclude_path(path, is_dir=True):
            try:
                children = []
                for child in path.iterdir():
                    if not self._should_exclude_path(child, is_dir=child.is_dir()):
                        children.append(child)
                
                # Sort: directories first, then files
                children.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
                
                extension = "    " if is_last else "│   "
                new_prefix = prefix + extension
                
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    lines.extend(self._generate_tree_structure(child, new_prefix, is_last_child))
                    
            except PermissionError:
                pass
        
        return lines
    
    def _get_file_content(self, file_path: Path) -> Optional[str]:
        """Get file content if it's a text file and not too large"""
        try:
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                return f"[File too large: {file_path.stat().st_size} bytes]"
            
            # Check if binary
            if self._is_binary_file(file_path):
                return None
            
            # Read content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            return f"[Error reading file: {e}]"
    
    def _collect_files(self, path: Path) -> List[Path]:
        """Collect all text files recursively"""
        files = []
        
        if path.is_file():
            if not self._should_exclude_path(path):
                files.append(path)
        elif path.is_dir() and not self._should_exclude_path(path, is_dir=True):
            try:
                for child in path.iterdir():
                    files.extend(self._collect_files(child))
            except PermissionError:
                pass
        
        return files
    
    def generate_dump(self) -> str:
        """Generate the complete markdown dump"""
        if not self.target_path.exists():
            raise FileNotFoundError(f"Path does not exist: {self.target_path}")
        
        lines = []
        
        # Header
        lines.append(f"# Project Dump: {self.target_path.name}")
        lines.append("")
        lines.append(f"Generated from: `{self.target_path}`")
        lines.append("")
        
        # Project structure
        lines.append("## Project Structure")
        lines.append("")
        lines.append("```")
        tree_lines = self._generate_tree_structure(self.target_path)
        lines.extend(tree_lines)
        lines.append("```")
        lines.append("")
        
        # File contents
        lines.append("## File Contents")
        lines.append("")
        
        # Collect all files
        all_files = self._collect_files(self.target_path)
        
        # Sort files by path
        all_files.sort(key=lambda x: str(x.relative_to(self.target_path)))
        
        for file_path in all_files:
            content = self._get_file_content(file_path)
            if content is not None:
                relative_path = file_path.relative_to(self.target_path)
                lines.append(f"### {relative_path}")
                lines.append("")
                
                if content.startswith("["):
                    # Error or special message
                    lines.append(content)
                else:
                    # Determine language for syntax highlighting
                    language = ""
                    ext = file_path.suffix.lower()
                    lang_map = {
                        '.py': 'python',
                        '.js': 'javascript',
                        '.ts': 'typescript',
                        '.jsx': 'jsx',
                        '.tsx': 'tsx',
                        '.html': 'html',
                        '.css': 'css',
                        '.scss': 'scss',
                        '.sass': 'sass',
                        '.json': 'json',
                        '.xml': 'xml',
                        '.yaml': 'yaml',
                        '.yml': 'yaml',
                        '.toml': 'toml',
                        '.ini': 'ini',
                        '.cfg': 'ini',
                        '.conf': 'conf',
                        '.sh': 'bash',
                        '.bash': 'bash',
                        '.zsh': 'zsh',
                        '.fish': 'fish',
                        '.ps1': 'powershell',
                        '.sql': 'sql',
                        '.md': 'markdown',
                        '.rst': 'rst',
                        '.tex': 'latex',
                        '.r': 'r',
                        '.rb': 'ruby',
                        '.php': 'php',
                        '.java': 'java',
                        '.c': 'c',
                        '.cpp': 'cpp',
                        '.cxx': 'cpp',
                        '.cc': 'cpp',
                        '.h': 'c',
                        '.hpp': 'cpp',
                        '.cs': 'csharp',
                        '.go': 'go',
                        '.rs': 'rust',
                        '.swift': 'swift',
                        '.kt': 'kotlin',
                        '.scala': 'scala',
                        '.clj': 'clojure',
                        '.elm': 'elm',
                        '.hs': 'haskell',
                        '.ml': 'ocaml',
                        '.fs': 'fsharp',
                        '.pl': 'perl',
                        '.lua': 'lua',
                        '.vim': 'vim',
                        '.dockerfile': 'dockerfile',
                    }
                    language = lang_map.get(ext, '')
                    
                    lines.append(f"```{language}")
                    lines.append(content)
                    lines.append("```")
                
                lines.append("")
        
        return "\n".join(lines)
