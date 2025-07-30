import csv
import sys
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlencode, urlparse, parse_qs
import click
import logging
import re
import shutil
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape, meta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

class Bookmark:
    """
    Represents a Raindrop.io bookmark and its metadata.

    Attributes:
        id (str): Unique identifier for the bookmark.
        title (str): Title of the bookmark.
        note (str): User note associated with the bookmark.
        excerpt (str): Excerpt or summary of the bookmark.
        url (str): URL of the bookmark.
        tags (str): Comma-separated tags.
        created (str): Creation date.
        cover (str): URL to the cover image.
        highlights (str): Highlights from the bookmark, separated by 'Highlight:'.
        favorite (str): 'true' if marked as favorite, else '' or 'false'.
    """
    def __init__(self, id: str, title: str, note: str, excerpt: str, url: str, tags: str, created: str, cover: str, highlights: str, favorite: str):
        self.id = id
        self.title = title or 'Untitled'
        self.note = note
        self.excerpt = excerpt
        self.url = url
        self.tags = tags
        self.created = created
        self.cover = cover
        self.highlights = highlights
        self.favorite = favorite

    def highlights_set(self):
        """
        Return a set of highlight strings for comparison.
        """
        if not self.highlights:
            return set()
        return set([h.strip() for h in self.highlights.split('Highlight:') if h.strip()])

    def to_markdown(self, template_name: str = None) -> str:
        """
        Convert the bookmark to a markdown string, optionally including YAML frontmatter with the template name.
        """
        frontmatter = ''
        if template_name:
            frontmatter = f"---\ntemplate: {template_name}\n---\n"
        md_lines = [frontmatter, f"## [{self.title}]({self.url})\n"]
        if self.cover:
            md_lines.append(f"![cover image]({self.cover})\n")
        if self.tags:
            tag_list = [f"#{tag.strip().replace(' ', '_')}" for tag in self.tags.split(',') if tag.strip()]
            md_lines.append(f"**Tags:** {' '.join(tag_list)}\n")
        if self.created:
            md_lines.append(f"**Created:** {self.created}\n")
        if self.favorite and self.favorite.lower() == 'true':
            md_lines.append(f"⭐ **Favorite**\n")
        if self.excerpt:
            md_lines.append(f"\n_Excerpt:_ {self.excerpt}\n")
        if self.note:
            md_lines.append(f"\n_Note:_ {self.note}\n")
        if self.highlights:
            highlight_lines = [h.strip() for h in self.highlights.split('Highlight:') if h.strip()]
            if highlight_lines:
                md_lines.append("\n### Highlights:\n")
                for h in highlight_lines:
                    md_lines.append(f"> {h}\n")
        md_lines.append("\n")
        return ''.join(md_lines)

    @staticmethod
    def from_markdown(md_block: str, template_path: Path = None) -> 'Bookmark':
        """
        Parse a markdown block and return a Bookmark object.
        Optionally checks for template frontmatter and parses fields based on the provided template.
        """
        import re
        from rich.panel import Panel
        from rich.console import Console
        console = Console()
        # Check YAML frontmatter for template
        frontmatter_match = re.match(r'^---\s*\ntemplate:\s*(.+?)\s*\n---\s*\n', md_block, re.DOTALL)
        template_in_note = None
        if frontmatter_match:
            template_in_note = frontmatter_match.group(1).strip()
            md_block = md_block[frontmatter_match.end():]  # Remove frontmatter for further parsing
        # If template_path is provided, check name
        if template_path is not None:
            expected_template = template_path.name
            if template_in_note and template_in_note != expected_template:
                console.print(Panel(f"[red]Template mismatch![/red]\nNote uses template: [bold]{template_in_note}[/bold]\nYou provided: [bold]{expected_template}[/bold]", title="[red]Error[/red]", style="red"))
                raise ValueError(f"Template mismatch: note uses {template_in_note}, provided {expected_template}")
        field_values = {
            'id': '', 'title': '', 'note': '', 'excerpt': '', 'url': '', 'tags': '', 'created': '', 'cover': '', 'highlights': '', 'favorite': ''
        }
        user_section_data = {}
        # Special handling for title+url in markdown link format
        title_url_match = re.search(r'^## \[(?P<title>.+?)\]\((?P<url>.+?)\)', md_block, re.MULTILINE)
        if title_url_match:
            field_values['title'] = title_url_match.group('title').strip()
            field_values['url'] = title_url_match.group('url').strip()
        # Use template if provided, else use a minimal default template
        if template_path and template_path.exists():
            template_vars = get_template_variables(template_path)
            user_sections = get_user_sections_from_template(template_path)
            with open(template_path, 'r', encoding='utf-8') as tf:
                template_lines = tf.readlines()
        else:
            template_vars = set(field_values.keys())
            user_sections = []
            # Minimal default template lines for fallback
            template_lines = [
                '## {{ title }}\n',
                '[Link]({{ url }})\n',
                'Created: {{ created }}\n',
                '⭐ Favorite\n',
                '> {{ excerpt }}\n',
                '_Note:_ {{ note }}\n',
                '**Tags:** {{ tags }}\n',
                '![cover image]({{ cover }})\n',
            ]

        # For each template variable, build a regex from the template line (robust Jinja2 replacement)
        for var in template_vars:
            if var == 'highlights':
                continue  # handled below
            # Find the template line containing the variable
            line_with_var = next((l for l in template_lines if f'{{{{ {var}' in l or f'{{{{{var}' in l), None)
            if not line_with_var:
                continue
            # Build regex: split on Jinja2 variable, escape before/after, insert capture group
            jinja_pattern = re.compile(r'\{\{\s*' + re.escape(var) + r'\s*\}\}')
            parts = jinja_pattern.split(line_with_var.strip())
            if len(parts) == 2:
                before, after = parts
                pattern = f'^{re.escape(before)}(?P<{var}>.+){re.escape(after)}$'
            else:
                # Fallback: just match the variable
                pattern = f'(?P<{var}>.+)'
            # Special case: allow for markdown blockquote for excerpt
            if var == 'excerpt' and line_with_var.strip().startswith('>'):
                pattern = r'^>\s*(?P<excerpt>.+)'
            # Special case: favorite is a flag, not a value
            if var == 'favorite':
                if re.search(pattern, md_block, re.MULTILINE):
                    field_values[var] = 'true'
                continue
            match = re.search(pattern, md_block, re.MULTILINE)
            if match and var in match.groupdict():
                field_values[var] = match.group(var).strip()
        # Special handling for highlights
        if 'highlights' in template_vars:
            highlights_list = []
            in_highlights = False
            for line in md_block.splitlines():
                if line.startswith('### Highlights:'):
                    in_highlights = True
                elif in_highlights and line.startswith('> '):
                    highlights_list.append(line[2:].strip())
                elif in_highlights and not line.startswith('> '):
                    in_highlights = False
            if highlights_list:
                field_values['highlights'] = 'Highlight:' + '\nHighlight:'.join(highlights_list)
        # User sections
        for section in user_sections:
            user_section_data[section] = extract_user_section(md_block, section)
        bm = Bookmark(
            id=field_values['id'],
            title=field_values['title'],
            note=field_values['note'],
            excerpt=field_values['excerpt'],
            url=field_values['url'],
            tags=field_values['tags'],
            created=field_values['created'],
            cover=field_values['cover'],
            highlights=field_values['highlights'],
            favorite=field_values['favorite']
        )
        bm.user_section_data = user_section_data
        return bm

def parse_raindrop_csv(csv_path: str) -> List[Bookmark]:
    """
    Parse a Raindrop.io CSV file and return a list of Bookmark objects.
    Handles file and CSV errors with rich output.
    """
    bookmarks = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            try:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    bookmark = Bookmark(
                        id=row.get('id', ''),
                        title=row.get('title', ''),
                        note=row.get('note', ''),
                        excerpt=row.get('excerpt', ''),
                        url=row.get('url', ''),
                        tags=row.get('tags', ''),
                        created=row.get('created', ''),
                        cover=row.get('cover', ''),
                        highlights=row.get('highlights', ''),
                        favorite=row.get('favorite', ''),
                    )
                    bookmarks.append(bookmark)
            except csv.Error as e:
                console.print(Panel(f"Failed to parse CSV file: [bold red]{csv_path}[/bold red]\n[red]{e}[/red]", title="[bold red]CSV Parse Error[/bold red]", style="red"))
                console.print("[yellow]Please check the CSV format and try again.[/yellow]")
                sys.exit(1)
    except FileNotFoundError:
        console.print(Panel(f"File not found: [bold red]{csv_path}[/bold red]", title="[bold red]File Not Found[/bold red]", style="red"))
        console.print("[yellow]Please check the path and try again.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(Panel(f"Unexpected error opening file: [bold red]{csv_path}[/bold red]\n[red]{e}[/red]", title="[bold red]File Error[/bold red]", style="red"))
        sys.exit(1)
    return bookmarks

def parse_markdown_file(md_path: str, template_path: Path = None) -> List[Bookmark]:
    """
    Parse an existing markdown file into a list of Bookmark objects.

    Args:
        md_path (str): Path to the markdown file to parse.
        template_path (Path, optional): Path to the Jinja2 template file used for parsing. If provided, checks for template match in frontmatter.

    Returns:
        List[Bookmark]: List of Bookmark objects parsed from the file. Returns an empty list if file is missing or unreadable.
    """
    if not Path(md_path).is_file():
        console.print(Panel(f"Markdown file not found: [bold red]{md_path}[/bold red]", title="[bold red]File Not Found[/bold red]", style="red"))
        console.print("[yellow]Please check the path and try again.[/yellow]")
        return []
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        console.print(Panel(f"Could not read markdown file: [bold red]{md_path}[/bold red]\n[red]{e}[/red]", title="[bold red]File Read Error[/bold red]", style="red"))
        return []
    import re
    # If no '## [' header, treat the whole file as a single block (legacy/edge case handling)
    if not re.search(r'^## \[', content, re.MULTILINE):
        blocks = [content]
    else:
        # Split into blocks, each starting with a bookmark header
        blocks = re.split(r'(?=^## \[)', content, flags=re.MULTILINE)
    bookmarks = []
    for block in blocks:
        if block.strip():
            try:
                bm = Bookmark.from_markdown(block, template_path=template_path)
                if bm.title and bm.url:
                    bookmarks.append(bm)
                else:
                    # Warn if block is missing required fields
                    console.print(Panel(f"Skipped malformed bookmark block: missing title or url.", title="[yellow]Warning[/yellow]", style="yellow"))
            except Exception as e:
                # Warn if block could not be parsed
                console.print(Panel(f"Failed to parse a bookmark block:\n[red]{e}[/red]", title="[yellow]Warning[/yellow]", style="yellow"))
    return bookmarks

def bookmarks_to_markdown(bookmarks: List[Bookmark]) -> str:
    """
    Convert a list of Bookmark objects to a single markdown string.

    Args:
        bookmarks (List[Bookmark]): List of Bookmark objects to convert.

    Returns:
        str: Markdown-formatted string representing all bookmarks.
    """
    md_lines = ["# Raindrop.io Bookmarks\n"]
    for bm in bookmarks:
        try:
            md_lines.append(bm.to_markdown())
        except Exception as e:
            # Warn if a bookmark could not be processed
            console.print(Panel(f"Error processing bookmark:\n[red]{e}[/red]", title="[yellow]Warning[/yellow]", style="yellow"))
            continue
    return ''.join(md_lines)

def write_markdown(md_content: str, md_path: str):
    """Write markdown content to file (create or update). Handles file write errors."""
    try:
        with open(md_path, 'w', encoding='utf-8') as mdfile:
            mdfile.write(md_content)
    except Exception as e:
        console.print(Panel(f"Failed to write markdown file: [bold red]{md_path}[/bold red]\n[red]{e}[/red]", title="[bold red]File Write Error[/bold red]", style="red"))
        sys.exit(1)

def list_bookmark_files(bookmark_dir: Path):
    """
    List all markdown files in the bookmark directory.
    Returns a sorted list of file paths.
    """
    if not bookmark_dir.exists() or not bookmark_dir.is_dir():
        console.print(Panel(f"Directory not found: [bold red]{bookmark_dir}[/bold red]", title="[red]Error[/red]", style="red"))
        return []
    files = sorted([f for f in bookmark_dir.iterdir() if f.suffix == ".md" and f.is_file()])
    if not files:
        console.print(Panel(f"No markdown files found in directory: [bold yellow]{bookmark_dir}[/bold yellow]", title="[yellow]Warning[/yellow]", style="yellow"))
    return files

def print_bookmarks_from_dir(bookmark_dir: Path):
    """
    Print a table of bookmarks in the directory, showing title, tags, creation date, and favorite status.
    """
    files = list_bookmark_files(bookmark_dir)
    if not files:
        console.print(f"[bold red]No bookmark files found in {bookmark_dir}.[/bold red]")
        return
    table = Table(title=f"Bookmarks in {bookmark_dir}")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Tags", style="magenta")
    table.add_column("Created", style="green")
    table.add_column("Favorite", style="yellow", justify="center")
    for i, f in enumerate(files, 1):
        with open(f, 'r', encoding='utf-8') as md:
            content = md.read()
        # Robustly extract title: try markdown link, fallback to first non-empty line, else filename
        title_match = re.search(r'## \[(.*?)\]', content)
        if title_match:
            title = title_match.group(1)
        else:
            # Try to find a line starting with '## ' and use the rest as title
            generic_title = re.search(r'^##\s+(.*)', content, re.MULTILINE)
            if generic_title:
                title = generic_title.group(1).strip()
            else:
                # Fallback: use the first non-empty line that isn't part of YAML frontmatter or a markdown symbol
                in_frontmatter = False
                title = f.name
                for line in content.splitlines():
                    line = line.strip()
                    if line == '---':
                        in_frontmatter = not in_frontmatter
                        continue
                    if in_frontmatter or not line:
                        continue
                    # Skip markdown symbols/headers except for single '# ' (treat as title)
                    if line.startswith('##'):
                        continue  # already handled above
                    if line.startswith('# '):
                        title = line[2:].strip() or f.name
                        break
                    if line.startswith(('#', '*', '-', '>', '`', '|', '[', '!', '_')):
                        continue
                    title = line
                    break
        tags = re.search(r'\*\*Tags:\*\* (.*)', content)
        tags = tags.group(1) if tags else ''
        created = re.search(r'\*\*Created:\*\* (.*)', content)
        created = created.group(1) if created else ''
        favorite = "⭐" if "⭐" in content else ""
        table.add_row(str(i), title, tags, created, favorite)
    console.print(table)

def remove_bookmark_interactive_dir(bookmark_dir: Path):
    """
    Interactively remove a bookmark file from the directory.
    Displays a list of bookmarks and prompts the user to select one to remove.
    """
    files = list_bookmark_files(bookmark_dir)
    if not files:
        console.print(Panel("No bookmark files found in [bold yellow]{}[/bold yellow].".format(bookmark_dir), title="[red]Error[/red]", style="red"))
        return
    console.print(Panel("Select a bookmark to remove:", title="[bold]Remove Bookmark[/bold]", style="yellow"))
    for i, f in enumerate(files, 1):
        with open(f, 'r', encoding='utf-8') as md:
            title = re.search(r'## \\[(.*?)\\]', md.read())
            title = title.group(1) if title else f.name
        console.print(f"[cyan]{i}.[/cyan] {title} ([dim]{f.name}[/dim])")
    try:
        choice = Prompt.ask("Enter the number to remove (0 to cancel)", default="0")
        choice = int(choice)
        if choice < 1 or choice > len(files):
            console.print(Panel("Cancelled or invalid selection.", title="[yellow]Cancelled[/yellow]", style="yellow"))
            return
        to_remove = files[choice-1]
        to_remove.unlink()
        console.print(Panel(f"Removed bookmark file: [bold green]{to_remove.name}[/bold green]", title="[green]Success[/green]", style="green"))
    except Exception as e:
        console.print(Panel(f"Invalid input or error: {e}", title="[red]Error[/red]", style="red"))

def edit_bookmark_interactive_dir(bookmark_dir: Path, templates_dir: Path):
    """
    Interactively edit a bookmark file in the directory.
    Displays a list of bookmarks and prompts the user to select one to edit.
    Opens the selected bookmark in a template for editing.
    """
    import re  # Ensure re is available
    files = list_bookmark_files(bookmark_dir)
    if not files:
        console.print(f"[bold red]No bookmark files found in {bookmark_dir}.[/bold red]")
        return

    # Display bookmarks for selection
    table = Table(title="Select a bookmark to edit", show_lines=True)
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Title", style="bold")
    table.add_column("File", style="dim")
    for i, f in enumerate(files, 1):
        with open(f, 'r', encoding='utf-8') as md:
            content = md.read()
        # Robustly extract title: try markdown link, fallback to first non-empty line, else filename
        title_match = re.search(r'## \[(.*?)\]', content)
        if title_match:
            title = title_match.group(1)
        else:
            # Try to find a line starting with '## ' and use the rest as title
            generic_title = re.search(r'^##\s+(.*)', content, re.MULTILINE)
            if generic_title:
                title = generic_title.group(1).strip()
            else:
                # Fallback: use the first non-empty line that isn't part of YAML frontmatter or a markdown symbol
                in_frontmatter = False
                title = f.name
                for line in content.splitlines():
                    line = line.strip()
                    if line == '---':
                        in_frontmatter = not in_frontmatter
                        continue
                    if in_frontmatter or not line:
                        continue
                    # Skip markdown symbols/headers except for single '# ' (treat as title)
                    if line.startswith('##'):
                        continue  # already handled above
                    if line.startswith('# '):
                        title = line[2:].strip() or f.name
                        break
                    if line.startswith(('#', '*', '-', '>', '`', '|', '[', '!', '_')):
                        continue
                    title = line
                    break
        table.add_row(str(i), title, f.name)
    console.print(table)

    try:
        choice = int(Prompt.ask("Enter the number to edit (0 to cancel)", default="0"))
        if choice < 1 or choice > len(files):
            console.print("[yellow]Cancelled or invalid selection.[/yellow]")
            return

        fpath = files[choice - 1]
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        # --- Read template name from frontmatter ---
        import re
        frontmatter_match = re.match(r'^---\s*\ntemplate:\s*(.+?)\s*\n---\s*\n', content, re.DOTALL)
        template_in_note = None
        if frontmatter_match:
            template_in_note = frontmatter_match.group(1).strip()
        else:
            console.print(Panel(f"[red]No template specified in frontmatter for {fpath.name}![/red]", title="[red]Error[/red]", style="red"))
            return
        template_path = templates_dir / template_in_note
        if not template_path.exists():
            console.print(Panel(f"[red]Template '{template_in_note}' referenced in note not found in templates folder![/red]", title="[red]Error[/red]", style="red"))
            return
        bm = Bookmark.from_markdown(content, template_path=template_path)

        # Determine template variables and user sections
        template_vars = RAINDROP_FIELDS
        user_section_data = {}
        if template_path and template_path.exists():
            template_vars = get_template_variables(template_path)
            user_sections = get_user_sections_from_template(template_path)
            for section in user_sections:
                user_section_data[section] = extract_user_section(content, section)

        # Show preview before editing
        console.print(Panel.fit(content, title=f"Editing: {bm.title}", subtitle=f"File: {fpath.name}"))

        # Prompt for editable fields
        field_prompts = [
            ('title', "Title"),
            ('note', "Note"),
            ('excerpt', "Excerpt"),
            ('tags', "Tags (comma separated)"),
            ('created', "Created"),
            ('cover', "Cover URL"),
            ('highlights', "Highlights (use 'Highlight:' as separator)"),
            ('favorite', "Favorite (true/false)")
        ]
        for attr, prompt_text in field_prompts:
            if attr in template_vars:
                current_value = getattr(bm, attr, '')
                setattr(bm, attr, Prompt.ask(prompt_text, default=current_value))

        # Prompt for user sections if present
        if template_path and template_path.exists():
            for section in user_section_data:
                user_section_data[section] = Prompt.ask(
                    f"{section.replace('_', ' ').title()}",
                    default=user_section_data[section]
                )
            md_content = render_bookmark_with_template(bm, template_path, user_section_data)
        else:
            md_content = bm.to_markdown()

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        console.print(f"[green]Updated bookmark:[/green] {bm.title} ({bm.url})")

    except Exception as e:
        console.print(Panel(f"Invalid input or error: {e}", title="[red]Error[/red]", style="red"))

def fuzzy_search_bookmarks_dir(bookmark_dir: Path, query: str, templates_dir: Path):
    """
    Perform a fuzzy search on bookmarks in the directory using the specified query.
    Displays matching bookmarks in a table.
    """
    bookmark_dir = Path(bookmark_dir)  # Ensure Path object
    templates_dir = Path(templates_dir)  # Ensure Path object
    files = list_bookmark_files(bookmark_dir)
    if not files:
        console.print(f"[bold red]No bookmark files found in {bookmark_dir}.[/bold red]")
        return
    from difflib import SequenceMatcher
    query_lower = query.lower()
    results = []
    for f in files:
        f = Path(f)  # Ensure Path object
        with open(str(f), 'r', encoding='utf-8') as md:
            content = md.read()
        # --- Read template name from frontmatter ---
        import re
        frontmatter_match = re.match(r'^---\s*\ntemplate:\s*(.+?)\s*\n---\s*\n', content, re.DOTALL)
        template_in_note = None
        if frontmatter_match:
            template_in_note = frontmatter_match.group(1).strip()
        else:
            console.print(Panel(f"[red]No template specified in frontmatter for {f.name}![/red]", title="[red]Error[/red]", style="red"))
            continue
        template_path = templates_dir / template_in_note
        if not template_path.exists():
            console.print(Panel(f"[red]Template '{template_in_note}' referenced in note not found in templates folder![/red]", title="[red]Error[/red]", style="red"))
            continue
        bm = Bookmark.from_markdown(content, template_path=template_path)
        fields = [bm.title, bm.url, bm.tags, bm.created, bm.favorite, bm.note, bm.highlights]
        def match_score(text):
            if not text:
                return 0
            text = str(text).lower()
            return SequenceMatcher(None, query_lower, text).ratio()
        score = max(match_score(fld) for fld in fields)
        if score > 0.3 or any(query_lower in str(fld).lower() for fld in fields if fld):
            results.append((score, bm, f.name, content))
    results.sort(reverse=True, key=lambda x: x[0])
    if not results:
        console.print(f"[yellow]No bookmarks matched the query: '{query}'[/yellow]")
        return
    table = Table(title=f"Search Results for '{query}'", show_lines=True)
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Tags", style="magenta")
    table.add_column("File", style="dim")
    table.add_column("%", style="blue", justify="right")
    for i, (score, bm, fname, content) in enumerate(results, 1):
        # Highlight query in title
        title_text = Text(bm.title)
        if query_lower in bm.title.lower():
            start = bm.title.lower().index(query_lower)
            title_text.stylize("bold red", start, start+len(query))
        tags = bm.tags
        percent = f"{int(score*100)}%"
        table.add_row(str(i), title_text, tags, fname, percent)
    console.print(table)

def sanitize_title(title: str):
    """
    Sanitize the bookmark title to make it filesystem-friendly.
    Removes non-alphanumeric characters, replaces spaces with underscores, and truncates to 40 characters.
    """
    sanitized = re.sub(r'[^\w\- ]', '', title).strip().replace(' ', '_')
    return sanitized[:40] or 'Untitled'

def zettelkasten_filename(bookmark: Bookmark) -> str:
    """
    Generate a Zettelkasten-style filename for the bookmark.
    Uses the creation date and time if available, otherwise falls back to the current date and time.
    """
    from datetime import datetime
    try:
        dt = datetime.strptime(bookmark.created, '%Y-%m-%d')
        # If no time, use 00:00
        dt = dt.replace(hour=0, minute=0)
    except Exception:
        dt = datetime.now()
    return f"{dt.strftime('%Y%m%d%H%M')}_{sanitize_title(bookmark.title)}.md"

def get_template_variables(template_path: Path) -> set:
    """
    Get the set of template variables used in the specified template.
    Returns a set of variable names (strings) that are used in the template.
    """
    env = get_template_env(template_path.parent)
    with open(template_path, 'r', encoding='utf-8') as f:
        source = f.read()
    parsed_content = env.parse(source)
    return meta.find_undeclared_variables(parsed_content)

RAINDROP_FIELDS = {
    'title', 'url', 'cover', 'tags', 'created', 'favorite', 'excerpt', 'note', 'highlights'
}

def get_user_sections_from_template(template_path: Path) -> list:
    """
    Get the list of user-defined sections in the template, excluding standard Raindrop fields.
    Returns a list of section names (strings) that are defined in the template but not in the standard Raindrop fields.
    """
    vars = get_template_variables(template_path)
    return [v for v in vars if v not in RAINDROP_FIELDS]

# Extract user section content from markdown by section name (e.g., 'user_notes')
def extract_user_section(md_content: str, section_name: str) -> str:
    """
    Extract the content of a user-defined section from the markdown content.
    Looks for '### Section Title' and grabs content until next header or EOF.
    """
    import re
    pattern = rf"###\s+{section_name.replace('_', ' ').title()}\n([\s\S]*?)(?=^### |\Z)"
    match = re.search(pattern, md_content, re.MULTILINE)
    return match.group(1).strip() if match else ''

def write_bookmarks_to_dir(bookmarks: List[Bookmark], out_dir: Path, template_path: Path = None):
    """
    Write the list of bookmarks to markdown files in the specified output directory.
    If a template path is provided, use it to render the bookmarks, otherwise use the default markdown format.
    """
    if not out_dir.exists():
        try:
            out_dir.mkdir(parents=True)
            console.print(Panel(f"Created output directory: [bold green]{out_dir}[/bold green]", title="[green]Success[/green]", style="green"))
        except Exception as e:
            console.print(Panel(f"Failed to create output directory: {e}", title="[red]Error[/red]", style="red"))
            sys.exit(1)
    overwrite_all = None  # None, True (yes to all), or False (no to all)
    # Build a map of base names (without timestamp) to existing files
    existing_files = {re.sub(r'^\d{8,}_', '', f.name): f for f in out_dir.glob('*.md')}
    user_sections = get_user_sections_from_template(template_path) if template_path else []
    template_name = template_path.name if template_path else None
    for bm in bookmarks:
        try:
            filename = zettelkasten_filename(bm)
            base_name = re.sub(r'^\d{8,}_', '', filename)
            file_path = out_dir / filename
            file_exists = base_name in existing_files
            user_section_data = {s: '' for s in user_sections}
            # If file exists, extract user section content
            if file_exists:
                existing_file_path = existing_files[base_name]
                with open(existing_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                for s in user_sections:
                    user_section_data[s] = extract_user_section(existing_content, s)
            # Optionally prompt for user section content on creation (can be skipped for now)
            if template_path and template_path.exists():
                md_content = render_bookmark_with_template(bm, template_path, user_section_data, template_name)
            else:
                md_content = bm.to_markdown(template_name=template_name)
            if file_exists:
                if overwrite_all is None:
                    panel = Panel(
                        f"File [bold yellow]{existing_file_path.name}[/bold yellow] already exists.\nUpdate to the new template? ([b]y[/b]/[b]n[/b]/[b]a[/b]=yes to all/[b]s[/b]=skip all)",
                        title="[yellow]File Exists[/yellow]", style="yellow")
                    console.print(panel)
                    resp = Prompt.ask("Your choice", choices=["y", "n", "a", "s"], default="n")
                    if resp == "a":
                        overwrite_all = True
                    elif resp == "s":
                        overwrite_all = False
                    elif resp == "y":
                        pass  # Overwrite this one
                    elif resp == "n":
                        console.print(Panel(f"Skipped: [bold]{existing_file_path.name}[/bold]", style="yellow"))
                        continue
                if overwrite_all is False:
                    console.print(Panel(f"Skipped: [bold]{existing_file_path.name}[/bold]", style="yellow"))
                    continue
                # If overwrite_all is True or user said y, overwrite
                with open(existing_file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                console.print(Panel(f"Updated: [bold green]{existing_file_path.name}[/bold green]", style="green"))
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                console.print(Panel(f"Created: [bold green]{filename}[/bold green]", style="green"))
        except Exception as e:
            console.print(Panel(f"Failed to write bookmark '{getattr(bm, 'title', 'Unknown')}' to file: {e}", title="[red]Error[/red]", style="red"))

def get_template_env(template_dir: Path):
    """
    Get the Jinja2 template environment for the specified directory.
    """
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['md', 'md.j2'])
    )

def render_bookmark_with_template(bookmark, template_path: Path, user_section_data: dict = None, template_name: str = None) -> str:
    """
    Render the bookmark using the specified template.
    Combines bookmark fields and user section data into the template context and renders it.
    """
    env = get_template_env(template_path.parent)
    template = env.get_template(template_path.name)
    # Prepare highlights as a list for the template
    highlights = []
    if bookmark.highlights:
        highlights = [h.strip() for h in bookmark.highlights.split('Highlight:') if h.strip()]
    context = dict(
        title=bookmark.title,
        url=bookmark.url,
        cover=bookmark.cover,
        tags=bookmark.tags,
        created=bookmark.created,
        favorite=bookmark.favorite and bookmark.favorite.lower() == 'true',
        excerpt=bookmark.excerpt,
        note=bookmark.note,
        highlights=highlights
    )
    if user_section_data:
        context.update(user_section_data)
    rendered = template.render(**context)
    # Add YAML frontmatter with template name
    if template_name:
        frontmatter = f"---\ntemplate: {template_name}\n---\n"
        return frontmatter + rendered
    return rendered

def create_or_update_markdown(csv_path: str, out_dir: Path, template_path: Path = None):
    """
    Parse CSV and write each bookmark to a separate markdown file in out_dir.
    If a template path is provided, use it to render the bookmarks, otherwise use the default markdown format.
    """
    csv_bookmarks = parse_raindrop_csv(csv_path)
    if not csv_bookmarks:
        console.print(Panel("No bookmarks found in the CSV file.", title="[red]Error[/red]", style="red"))
        sys.exit(1)
    write_bookmarks_to_dir(csv_bookmarks, out_dir, template_path)
    console.print(Panel(f"Bookmark files created/updated in: [bold green]{out_dir}[/bold green]", title="[green]Success[/green]", style="green"))

@click.group()
def cli():
    """Raindrop.io CSV to Markdown CLI (zettelkasten mode)"""
    pass

def get_templates_folder() -> Path:
    """
    Always get the templates folder from the current working directory.
    Exits the program if the templates folder does not exist.
    """
    templates_dir = Path.cwd() / "templates"
    if not templates_dir.exists() or not templates_dir.is_dir():
        console.print(Panel(f"[red]No templates/ folder found in {templates_dir}![/red]", title="[red]Error[/red]", style="red"))
        sys.exit(1)
    return templates_dir

def select_template_interactive(templates_dir: Path) -> Path:
    """
    Interactively select a template file from the templates directory.
    Displays a list of available templates and prompts the user to select one.
    """
    templates = list(templates_dir.glob("*.md.j2"))
    if not templates:
        console.print(Panel(f"[red]No templates found in {templates_dir}![/red]", title="[red]Error[/red]", style="red"))
        sys.exit(1)
    console.print(Panel("Select a template to use:", title="[bold]Template Selection[/bold]", style="cyan"))
    for i, t in enumerate(templates, 1):
        console.print(f"[cyan]{i}.[/cyan] {t.name}")
    idx = int(Prompt.ask("Enter the number of the template", default="1"))
    if idx < 1 or idx > len(templates):
        console.print("[yellow]Invalid selection. Aborting.[/yellow]")
        sys.exit(1)
    return templates[idx-1]

@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--template', 'template_path', type=click.Path(exists=True), default=None, help='Path to a custom markdown template file.')
def create(csv_file, output_dir, template_path):
    """Parse CSV_FILE and create/update one markdown file per bookmark in OUTPUT_DIR."""
    out_dir = Path(output_dir)
    templates_dir = get_templates_folder()
    tpl_path = Path(template_path) if template_path else select_template_interactive(templates_dir)
    create_or_update_markdown(csv_file, out_dir, tpl_path)

@cli.command('list')
@click.argument('bookmark_dir', type=click.Path(exists=True, file_okay=False))
def list(bookmark_dir):
    """Display all bookmarks in BOOKMARK_DIR."""
    print_bookmarks_from_dir(Path(bookmark_dir))

@cli.command('remove')
@click.argument('bookmark_dir', type=click.Path(exists=True, file_okay=False))
def remove(bookmark_dir):
    """Interactively remove a bookmark file from BOOKMARK_DIR."""
    remove_bookmark_interactive_dir(Path(bookmark_dir))

@cli.command('edit')
@click.argument('bookmark_dir', type=click.Path(exists=True, file_okay=False))
def edit(bookmark_dir):
    """Interactively edit a bookmark file in BOOKMARK_DIR."""
    templates_dir = get_templates_folder()
    edit_bookmark_interactive_dir(Path(bookmark_dir), templates_dir)

@cli.command('find')
@click.argument('bookmark_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('query', type=str)
def find(bookmark_dir, query):
    try:
        bookmark_dir = Path(bookmark_dir)  # Convert to Path object inside the function
        templates_dir = get_templates_folder()
        templates = [f for f in templates_dir.iterdir() if f.is_file() and f.name.endswith('.md.j2')]
        if len(templates) == 0:
            console.print(Panel(f"[red]No templates found in {templates_dir}![/red]", title="[red]Error[/red]", style="red"))
            sys.exit(1)
        fuzzy_search_bookmarks_dir(bookmark_dir, query, templates_dir=templates_dir)
    except Exception as e:
        console.print(Panel(f"[red]Error in 'find' command: {e}[/red]", title="[red]Find Command Error[/red]", style="red"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cli()