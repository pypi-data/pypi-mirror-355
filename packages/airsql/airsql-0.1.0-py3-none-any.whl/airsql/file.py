"""
File class for representing SQL files with Jinja templating support.
"""

import inspect
from pathlib import Path
from typing import Any, Dict, Optional


def _get_caller_dag_directory() -> Optional[str]:
    """
    Get the directory of the DAG file that's calling the File class.

    Returns:
        The directory path of the calling DAG file, or None if not found.
    """
    frame = inspect.currentframe()
    try:
        # Walk up the call stack to find the DAG file
        while frame:
            filename = frame.f_code.co_filename
            # Look for files in dag_definitions or similar DAG directories
            if (
                'dag_definitions' in filename
                or 'dags' in filename
                or filename.endswith('_dag.py')
                or filename.endswith('_pipeline.py')
            ):
                return str(Path(filename).parent)
            frame = frame.f_back
        return None
    finally:
        del frame


class File:
    """
    Represents a SQL file with optional Jinja templating.

    Examples:
        # Simple SQL file
        File("queries/user_analysis.sql")

        # SQL file with Jinja variables
        File("queries/date_range_report.sql", variables={"start_date": "2025-01-01"})

        # SQL file with custom base path
        File("user_analysis.sql", base_path="/path/to/sql/files")
    """

    def __init__(
        self,
        file_path: str,
        variables: Optional[Dict[str, Any]] = None,
        base_path: Optional[str] = None,
    ):
        self.file_path = file_path
        self.variables = variables or {}
        self.base_path = base_path
        self._content: Optional[str] = None

    @property
    def full_path(self) -> Path:
        """
        Get the full path to the SQL file.

        First tries to find the file relative to the calling DAG's directory,
        then falls back to the base_path or default 'sql' directory.
        """
        # If it's an absolute path, use it directly
        if Path(self.file_path).is_absolute():
            return Path(self.file_path)

        # If base_path is explicitly provided, use it
        if self.base_path:
            return Path(self.base_path) / self.file_path

        # Try to find the file relative to the calling DAG's directory
        dag_directory = _get_caller_dag_directory()
        if dag_directory:
            local_sql_path = Path(dag_directory) / self.file_path
            if local_sql_path.exists():
                return local_sql_path

        # Fall back to the default 'sql' directory
        return Path('sql') / self.file_path

    def read_content(self) -> str:
        """Read the SQL file content."""
        if self._content is None:
            if not self.full_path.exists():
                raise FileNotFoundError(f'SQL file not found: {self.full_path}')

            self._content = self.full_path.read_text(encoding='utf-8')

        return self._content

    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render the SQL file with Jinja templating.

        Args:
            context: Additional context variables for Jinja rendering

        Returns:
            Rendered SQL string
        """
        # Check if it's an absolute path
        if Path(self.file_path).is_absolute():
            sql_path = Path(self.file_path)
            if not sql_path.exists():
                raise FileNotFoundError(f'SQL file not found: {sql_path}')
            sql_content = sql_path.read_text(encoding='utf-8')
        else:
            # Try to find the file relative to the calling DAG's directory
            dag_directory = _get_caller_dag_directory()
            local_sql_path = None

            if dag_directory:
                local_sql_path = Path(dag_directory) / self.file_path
                if local_sql_path.exists():
                    sql_content = local_sql_path.read_text(encoding='utf-8')
                else:
                    local_sql_path = None

            if not local_sql_path:
                # Fall back to using the same Jinja environment as decorators
                try:
                    from jinja2 import (  # noqa: PLC0415
                        Environment,
                        FileSystemLoader,
                        select_autoescape,
                    )

                    # Use same search paths as decorators
                    search_paths = ['dags/git_sql', 'sql/']

                    # Create Jinja environment with multiple search paths
                    env = Environment(
                        loader=FileSystemLoader(search_paths),
                        autoescape=select_autoescape(['html', 'xml']),
                    )

                    # Try to load the template
                    template = env.get_template(self.file_path)
                    sql_content = template.source

                except Exception as e:
                    search_paths_str = ', '.join(['DAG directory'] + search_paths)
                    raise FileNotFoundError(
                        f'SQL file not found: {self.file_path}. '
                        f'Searched in: {search_paths_str}'
                    ) from e

        # Render with Jinja if variables are present
        if not self.variables and not context:
            return sql_content

        try:
            from jinja2 import Template  # noqa: PLC0415
        except ImportError:
            raise ImportError(
                'Jinja2 is required for SQL file templating. '
                'Install it with: pip install jinja2'
            )

        template_vars = {**self.variables}
        if context:
            template_vars.update(context)

        template = Template(sql_content)
        return template.render(**template_vars)

    def __str__(self) -> str:
        """Return the rendered SQL content."""
        return self.render()

    def __repr__(self) -> str:
        return f"File(file_path='{self.file_path}')"
