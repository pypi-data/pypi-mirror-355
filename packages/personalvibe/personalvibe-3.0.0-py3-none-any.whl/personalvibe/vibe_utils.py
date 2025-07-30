# Copyright © 2025 by Nick Jenkins. All rights reserved
# mypy: ignore-errors
import fnmatch
import hashlib
import html
import logging
import logging as _pv_log
import os
import random
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, List, Union

import dotenv
import pathspec
import tiktoken
from jinja2 import Environment, FileSystemLoader

from personalvibe import llm_router  # ← LiteLLM shim (chunk-3)

if TYPE_CHECKING:
    from personalvibe.run_pipeline import ConfigModel  # noqa: F401

from personalvibe.yaml_utils import sanitize_yaml_text

dotenv.load_dotenv()
# -----------------------------------------------------------------
# Ensure wheel smoke-tests never abort if the user forgot to export
# an OPENAI key – we create a harmless placeholder *once*.


log = logging.getLogger(__name__)


def get_prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def rainbow(text: str) -> str:
    """Return the text with each character wrapped in a cycling rainbow colour."""
    RAINBOW_COLORS = [31, 33, 32, 36, 34, 35]  # red, yellow, green, cyan, blue, magenta
    wrapped = []
    _ = len(RAINBOW_COLORS)
    for ch in text:
        color = random.choice(RAINBOW_COLORS)
        wrapped.append(f"\033[{color}m{ch}\033[0m")
    return "".join(wrapped)


def find_existing_hash(root_dir: Union[str, Path], hash_str: str) -> Union[Path, None]:
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if hash_str in filename:
                return Path(dirpath) / filename
    return None


def save_prompt(prompt: str, root_dir: Path, input_hash: str = "") -> Path:
    """Persist *one* prompt to disk and return its Path.

    Behaviour
    ----------
    • Uses SHA-256(prompt)[:10] to create a stable short-hash.
    • If a file containing that hash already exists, nothing is written
      and the *existing* Path is returned.
    • New files are named   <timestamp>[_<input_hash>]_ <hash>.md
    • Every file is terminated with an extra line::

          ### END PROMPT

      to make `grep -A999 '^### END PROMPT$'` trivially reliable.
    """
    # Timestamp + hash bits
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    hash_str = get_prompt_hash(prompt)[:10]

    if existing := find_existing_hash(root_dir, hash_str):
        log.info("Duplicate prompt detected. Existing file: %s", existing)
        return existing

    # Compose filename
    if input_hash:
        filename = f"{timestamp}_{input_hash}_{hash_str}.md"
    else:
        filename = f"{timestamp}_{hash_str}.md"
    filepath = Path(root_dir) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write prompt + END-marker
    filepath.write_text(
        f"""{prompt}
### END PROMPT
""",
        encoding="utf-8",
    )
    log.info("Prompt saved to: %s", filepath)
    return filepath


def get_vibed(
    prompt: str,
    contexts: Union[List[Path], None] = None,
    project_name: str = "",
    model: Union[str, None] = None,
    max_completion_tokens: int = 100_000,
    *,
    workspace: Union[Path, None] = None,
) -> str:
    """Wrapper for O3 vibecoding – **now workspace-aware**."""
    if contexts is None:
        contexts = []

    workspace = workspace or get_workspace_root()

    base_input_path = get_data_dir(project_name, workspace) / "prompt_inputs"
    base_input_path.mkdir(parents=True, exist_ok=True)
    prompt_file = save_prompt(prompt, base_input_path)
    input_hash = prompt_file.stem.split("_")[-1]

    # -- build messages ---------------------------------------------------
    messages = []
    for context in contexts:
        part = {"role": "user" if "prompt_inputs" in context.parts else "assistant"}
        part["content"] = [{"type": "text", "text": context.read_text()}]
        messages.append(part)

    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

    message_chars = len(str(messages))
    model = model or "openai/o3"
    message_tokens = num_tokens(str(messages))
    log.info("Prompt size – Tokens: %s, Chars: %s, Model:%s", message_tokens, message_chars, model)

    resp = llm_router.chat_completion(
        model=model,
        messages=messages,
        max_tokens=max_completion_tokens,
    )
    response = resp["choices"][0]["message"]["content"]

    # -- save assistant reply --------------------------------------------
    base_output_path = get_data_dir(project_name, workspace) / "prompt_outputs"
    base_output_path.mkdir(parents=True, exist_ok=True)
    _ = save_prompt(response, base_output_path, input_hash=input_hash)

    return response


COMMENT_PREFIX = "#"
EXCLUDE_PREFIX = "X "
WILDCARD_CHARS = "*?[]"


def _expand_pattern(base: Path, pattern: str) -> Iterable[Path]:
    """Return paths matching *pattern* relative to *base* (handles “…/**”)."""
    pat = pattern.lstrip("/")
    if pat.endswith("/**"):
        pat = f"{pat}/*"
    yield from base.glob(pat)


def get_context(filenames: List[str], extension: str = ".txt") -> str:  # type: ignore[override]  # noqa: D401
    """
    Concatenate the contents of every file referenced in *filenames*.

    Features
    --------
    • Comment lines (`# …`) and blanks ignored.
    • Manual excludes:  `X <glob>` (evaluated *before* any include).
    • Wildcards allowed; directories are recursed.
    • Respects `.gitignore` via ``load_gitignore``.
    • Never rewrites the config files in-place.
    """
    from personalvibe.vibe_utils import (  # late import avoids cycles
        _process_file,
        get_base_path,
        load_gitignore,
    )

    base_path = get_base_path()
    gitignore_spec = load_gitignore(base_path)

    manual_excludes: list[str] = []
    include_lines: list[str] = []

    # --------------------------------------------------------
    # ❶  Parse every config file – first collect, don’t act.
    # --------------------------------------------------------
    for name in filenames:
        cfg_path = base_path / name
        if not cfg_path.exists():
            log.warning("Config file %s is missing (cwd=%s)", cfg_path, os.getcwd())
            continue

        for raw in cfg_path.read_text("utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith(COMMENT_PREFIX):
                continue
            if line.startswith(EXCLUDE_PREFIX):
                manual_excludes.append(line[len(EXCLUDE_PREFIX) :].strip().lstrip("/"))
            else:
                include_lines.append(line.lstrip("/"))

    # normalise manual_excludes once
    manual_excludes = [p or "**" for p in manual_excludes]

    # --------------------------------------------------------
    # ❷  Helper that applies *all* exclude logic in one place
    # --------------------------------------------------------
    def _maybe_add(path: Path, *, rel: Union[str, None] = None) -> None:
        nonlocal big_string
        rel = rel or str(path.relative_to(base_path))
        if (
            not path.is_file()
            or gitignore_spec.match_file(rel)
            or any(fnmatch.fnmatch(rel, pat) for pat in manual_excludes)
        ):
            return
        try:
            big_string += _process_file(path)
        except UnicodeDecodeError:
            log.error("Unicode error reading %s", rel)

    # --------------------------------------------------------
    # ❸  Process includes now that excludes are known
    # --------------------------------------------------------
    big_string = ""
    for line in include_lines:
        # glob / wildcard include
        if any(ch in line for ch in WILDCARD_CHARS):
            for match in _expand_pattern(base_path, line):
                if match.is_dir():
                    for f in match.rglob("*"):
                        _maybe_add(f)
                else:
                    _maybe_add(match)
        # explicit path include
        else:
            path = base_path / line
            if not path.exists():
                raise ValueError(f"Warning: {path} does not exist (cwd={os.getcwd()})")
            if path.is_dir():
                for f in path.rglob("*"):
                    _maybe_add(f)
            else:
                _maybe_add(path)

    return big_string


def _process_file(file_path: Path) -> str:
    """Helper to read and return file content with appropriate markdown code fences."""
    rel_path = file_path.relative_to(get_base_path())
    extension = file_path.suffix.lower()

    # Map file extensions to markdown languages
    extension_to_lang = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".json": "json",
        ".html": "html",
        ".md": "",  # Markdown files don’t need code fences, show raw content
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "",  # Plain text, no code highlighting
        ".sh": "bash",
        ".cfg": "",
        ".ini": "",
    }

    language = extension_to_lang.get(extension, "")  # Default to no highlighting if unknown

    content = file_path.read_text(encoding="utf-8")
    content = html.unescape(content)

    if extension == ".md":
        # For markdown files, don't wrap in code fences
        return f"\n#### Start of {rel_path}\n{content}\n#### End of {rel_path}\n"
    else:
        return f"\n#### Start of {rel_path}\n" f"```{language}\n" f"{content}\n" f"```\n" f"#### End of {rel_path}\n"


def load_gitignore(base_path: Path) -> pathspec.PathSpec:
    gitignore_path = base_path / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", f)
        return spec
    return pathspec.PathSpec([])  # Empty spec if no .gitignore


_SENTINEL_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def get_workspace_root() -> Path:
    """Return the directory where **runtime artefacts** should live.

    Resolution order
    ----------------
    1. Environment variable ``PV_DATA_DIR`` (if set & non-empty)
    2. **Mono-repo fallback** – if the current process is running from
       within the original Personalvibe source checkout (detected by the
       presence of *prompts/* beside ``src/``), we keep the *old* behaviour
       so that developer workflows stay unchanged.
    3. Finally, just ``Path.cwd()`` (suits ``pip install personalvibe`` in
       any third-party project).
    """
    env = os.getenv("PV_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()

    # inside mono-repo?  -> use legacy base-path crawl
    if _SENTINEL_PROMPTS_DIR.exists():
        from warnings import warn

        warn(
            "⚠️  get_workspace_root() fell back to repo-root because "
            "$PV_DATA_DIR is unset and prompts/ directory exists.  "
            "Set PV_DATA_DIR to silence this message.",
            stacklevel=2,
        )
        return get_base_path()  # type: ignore[arg-type]

    # default
    return Path.cwd().resolve()


def get_data_dir(project_name: str, workspace: Union[Path, None] = None) -> Path:
    """<workspace>/data/<project_name> (mkdir-p, but *not* the sub-folders)."""
    root = workspace or get_workspace_root()
    p = root / "data" / project_name
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_logs_dir(workspace: Union[Path, None] = None) -> Path:
    """<workspace>/logs  (mkdir-p)."""
    root = workspace or get_workspace_root()
    p = root / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_base_path(base: str = "personalvibe") -> Path:
    """Returns the base folder directory for the entire github project."""
    new_parts = []
    for part in Path(os.getcwd()).parts:
        new_parts.append(part)
        if part == base:
            break
    return Path(*new_parts)


def num_tokens(text: str) -> int:
    """Just use o3 for a rough guide."""
    enc = tiktoken.encoding_for_model("o3")
    return len(enc.encode(text))


def _get_error_text(config: "ConfigModel") -> str:
    error_path = Path(get_base_path(), "prompts", config.project_name, "errors", config.error_file_name)
    # NOTE TO LLM: improve the handling here as per my usual codestyle
    return error_path.read_text()


def _get_milestone_text(config: "ConfigModel") -> str:
    stages_path = Path(get_base_path(), "prompts", config.project_name, "stages")
    milestone_ver, _, _ = config.version.split(".")
    current_major = int(milestone_ver)

    milestone_files = [Path(stages_path, f"{current_major}.0.0.md")]

    if not milestone_files:
        raise ValueError(f"No valid milestone files found in {stages_path} for major <= {current_major}")
    data = """The following are all milestones related to this project.
    The latest milestone text proposes next work needed, this is what sprints focus on:
    """
    data += "\n\n".join(p.read_text() for p in milestone_files)
    return data


def _load_template(fname: str) -> str:
    """Return the *text* of a template shipped as package-data.

    Resolution order
    ----------------
    1. `importlib.resources.files('personalvibe.data')/fname`
    2. Legacy path  src/personalvibe/commands/<fname>
    """
    try:
        pkg_file = resources.files("personalvibe.data").joinpath(fname)
        return pkg_file.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        legacy = Path(__file__).parent / "data" / fname
        if legacy.exists():
            log.debug("Template %s loaded from legacy path %s", fname, legacy)
            return legacy.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Template {fname!s} not found in package or legacy path")


def get_replacements(config: "ConfigModel", project_context: str) -> dict:
    """Build the Jinja replacement map using task-based configuration."""
    from personalvibe.task_config import task_manager

    log.info("Running config version: %s", config.version)
    log.info("Running task: %s", config.task)

    # Load task configuration
    try:
        task_config = task_manager.load_task_config(config.task)
    except ValueError as e:
        log.error("Failed to load task config: %s", e)
        raise

    # Build context for task instruction rendering
    task_context = {
        "project_name": config.project_name,
        "version": config.version,
    }

    # Handle task-specific context requirements
    if config.task == "validate" and config.error_file_name:
        task_context["error_details"] = _get_error_text(config)

    # Attempt to get milestone text
    try:
        task_context["milestone_text"] = _get_milestone_text(config)
    except Exception as e:
        log.warning("Could not load milestone text: %s", e)
        task_context["milestone_text"] = ""

    # Render task instructions with context
    task_instructions = task_manager.render_task_instructions(task_config, task_context)

    return {
        "project_name": config.project_name,
        "task_summary": task_config.task_summary,
        "user_instructions": config.user_instructions,
        "task_instructions": task_instructions,
        "project_context": project_context,
    }


def detect_project_name(cwd: Union[Path, None] = None) -> str:
    """Best-effort inference of the **project_name**.

    Strategy
    --------
    1. If *cwd* (or its parents) path contains ``prompts/<name>`` → return
       that immediate directory name.
    2. Else walk *upwards* until a folder with ``prompts/`` is found:
         • if that ``prompts`` dir contains exactly ONE sub-directory we
           assume it is the project.
    3. Otherwise raise ``ValueError`` explaining how to fix.

    This keeps the common cases zero-config while remaining explicit when
    multiple projects coexist.
    """
    cwd = (cwd or Path.cwd()).resolve()
    parts = cwd.parts
    if "prompts" in parts:
        idx = parts.index("prompts")
        if idx + 1 < len(parts):
            return parts[idx + 1]

    for parent in [cwd, *cwd.parents]:
        p_dir = parent / "prompts"
        if p_dir.is_dir():
            sub = [d for d in p_dir.iterdir() if d.is_dir()]
            if len(sub) == 1:
                return sub[0].name
            break  # ambiguous – fallthrough to error
    raise ValueError(
        "Unable to auto-detect project_name; pass --project_name or run " "from within prompts/<name>/… directory."
    )
