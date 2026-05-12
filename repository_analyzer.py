"""
DeployBuddy Repository Intelligence
===================================
Membaca repository aplikasi user sebelum RAG arsitektur berjalan.

Tujuannya sederhana: jangan biarkan LLM menebak stack. Modul ini membaca
manifest, config deployment, dan snippet kode terpilih untuk membuat profil
repository yang bisa di-inject ke prompt RAG 1.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


DEFAULT_MAX_FILES = 80
DEFAULT_MAX_SNIPPETS = 20
DEFAULT_MAX_FILE_SIZE_BYTES = 200 * 1024
DEFAULT_SNIPPET_CHARS = 4000

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "out",
    "target",
    "coverage",
    ".turbo",
    ".cache",
}

SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

SENSITIVE_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
    ".sqlite",
    ".sqlite3",
    ".db",
}

IMPORTANT_FILE_NAMES = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "go.mod",
    "go.sum",
    "cargo.toml",
    "composer.json",
    "gemfile",
    "pom.xml",
    "build.gradle",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "vercel.json",
    "netlify.toml",
    "railway.json",
    "render.yaml",
    "firebase.json",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "vite.config.js",
    "vite.config.ts",
    "nuxt.config.ts",
    "svelte.config.js",
    ".env.example",
    "env.example",
}

SOURCE_SUFFIXES = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".go",
    ".java",
    ".kt",
    ".php",
    ".rb",
    ".rs",
    ".cs",
    ".scala",
    ".swift",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".xml",
}

ENTRYPOINT_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "asgi.py",
    "wsgi.py",
    "main.go",
    "server.go",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "app.js",
    "app.ts",
    "route.ts",
    "route.js",
    "api.ts",
    "api.js",
}


class RepositoryAnalysisError(RuntimeError):
    """Raised when repository analysis cannot be completed."""


@dataclass
class CodeSnippet:
    path: str
    language: str
    reason: str
    content: str


@dataclass
class RepositoryProfile:
    source: str
    root_path: str
    detected_stack: List[str] = field(default_factory=list)
    service_types: List[str] = field(default_factory=list)
    runtimes: List[str] = field(default_factory=list)
    frameworks: Dict[str, List[str]] = field(default_factory=dict)
    databases: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)
    important_files: List[str] = field(default_factory=list)
    dependency_summary: Dict[str, List[str]] = field(default_factory=dict)
    architecture_hints: List[str] = field(default_factory=list)
    snippets: List[CodeSnippet] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_count_scanned: int = 0

    def to_stack_string(self) -> str:
        parts = []
        if self.detected_stack:
            parts.append(", ".join(self.detected_stack))
        if self.runtimes:
            parts.append("Runtimes: " + ", ".join(self.runtimes))
        if self.databases:
            parts.append("Databases: " + ", ".join(self.databases))
        if self.service_types:
            parts.append("Services: " + ", ".join(self.service_types))
        return " | ".join(parts)

    def to_json(self) -> Dict:
        return {
            "source": self.source,
            "detected_stack": self.detected_stack,
            "service_types": self.service_types,
            "runtimes": self.runtimes,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "package_managers": self.package_managers,
            "important_files": self.important_files,
            "dependency_summary": self.dependency_summary,
            "architecture_hints": self.architecture_hints,
            "warnings": self.warnings,
            "file_count_scanned": self.file_count_scanned,
        }

    def to_context(self, max_chars: int = 18000) -> str:
        lines = [
            "=== REPOSITORY ANALYSIS CONTEXT ===",
            f"Source: {self.source}",
            f"Files scanned: {self.file_count_scanned}",
            f"Detected stack: {', '.join(self.detected_stack) or 'None detected'}",
            f"Service types: {', '.join(self.service_types) or 'None detected'}",
            f"Runtimes: {', '.join(self.runtimes) or 'None detected'}",
            f"Databases: {', '.join(self.databases) or 'None detected'}",
            f"Package managers: {', '.join(self.package_managers) or 'None detected'}",
            "",
            "Frameworks by layer:",
        ]
        for layer, names in self.frameworks.items():
            lines.append(f"- {layer}: {', '.join(names)}")
        if not self.frameworks:
            lines.append("- None detected")

        lines.extend(["", "Architecture hints:"])
        lines.extend(f"- {hint}" for hint in self.architecture_hints) if self.architecture_hints else lines.append("- None")

        lines.extend(["", "Important files:"])
        lines.extend(f"- {path}" for path in self.important_files[:30]) if self.important_files else lines.append("- None")

        lines.extend(["", "Dependency summary:"])
        for source, deps in self.dependency_summary.items():
            preview = ", ".join(deps[:25])
            if len(deps) > 25:
                preview += f", ... (+{len(deps) - 25} more)"
            lines.append(f"- {source}: {preview}")
        if not self.dependency_summary:
            lines.append("- None")

        if self.warnings:
            lines.extend(["", "Warnings:"])
            lines.extend(f"- {warning}" for warning in self.warnings)

        lines.extend(["", "Selected code/config snippets:"])
        for snippet in self.snippets:
            lines.append(f"\n--- {snippet.path} ({snippet.reason}) ---")
            lines.append(f"```{snippet.language}")
            lines.append(snippet.content)
            lines.append("```")

        context = "\n".join(lines)
        if len(context) > max_chars:
            return context[:max_chars] + "\n\n[Repository context truncated to fit prompt budget]"
        return context

    def print_summary(self):
        print("\n" + "=" * 70)
        print("DEPLOYBUDDY - REPOSITORY ANALYSIS")
        print("=" * 70)
        print(f"Source       : {self.source}")
        print(f"Files scanned: {self.file_count_scanned}")
        print(f"Stack        : {', '.join(self.detected_stack) or 'None detected'}")
        print(f"Services     : {', '.join(self.service_types) or 'None detected'}")
        print(f"Databases    : {', '.join(self.databases) or 'None detected'}")
        if self.architecture_hints:
            print("Hints        :")
            for hint in self.architecture_hints:
                print(f"  - {hint}")


class RepositoryAnalyzer:
    def __init__(
        self,
        max_files: int = DEFAULT_MAX_FILES,
        max_snippets: int = DEFAULT_MAX_SNIPPETS,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
        snippet_chars: int = DEFAULT_SNIPPET_CHARS,
    ):
        self.max_files = max_files
        self.max_snippets = max_snippets
        self.max_file_size_bytes = max_file_size_bytes
        self.snippet_chars = snippet_chars

    def analyze_path(self, repo_path: str, source: Optional[str] = None) -> RepositoryProfile:
        root = Path(repo_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise RepositoryAnalysisError(f"Repository path not found or not a directory: {repo_path}")

        candidates = self._collect_candidate_files(root)
        selected = candidates[: self.max_files]
        if len(candidates) > self.max_files:
            warning = f"Repository has {len(candidates)} readable candidate files; analyzed first {self.max_files} by priority."
        else:
            warning = ""

        state = _DetectionState()
        snippets: List[CodeSnippet] = []
        important_files: List[str] = []

        for file_path, reason, priority in selected:
            rel_path = _relative_posix(file_path, root)
            content = self._read_text_file(file_path)
            if content is None:
                continue

            state.file_count += 1
            if priority <= 1:
                important_files.append(rel_path)

            self._analyze_file(rel_path, content, state)

            if len(snippets) < self.max_snippets and (priority <= 1 or self._looks_like_entrypoint(rel_path, content)):
                snippets.append(
                    CodeSnippet(
                        path=rel_path,
                        language=_language_for_path(rel_path),
                        reason=reason,
                        content=content[: self.snippet_chars],
                    )
                )

        warnings = [warning] if warning else []
        profile = RepositoryProfile(
            source=source or str(root),
            root_path=str(root),
            detected_stack=sorted(state.stack),
            service_types=sorted(state.service_types),
            runtimes=sorted(state.runtimes),
            frameworks={layer: sorted(names) for layer, names in sorted(state.frameworks.items()) if names},
            databases=sorted(state.databases),
            package_managers=sorted(state.package_managers),
            important_files=important_files,
            dependency_summary={key: sorted(values) for key, values in sorted(state.dependencies.items())},
            architecture_hints=self._build_architecture_hints(state),
            snippets=snippets,
            warnings=warnings,
            file_count_scanned=state.file_count,
        )
        return profile

    def _collect_candidate_files(self, root: Path) -> List[Tuple[Path, str, int]]:
        candidates: List[Tuple[Path, str, int]] = []
        for current_root, dir_names, file_names in os.walk(root):
            dir_names[:] = [
                name for name in dir_names
                if name.lower() not in IGNORED_DIRS and not name.startswith(".git")
            ]
            current = Path(current_root)
            for file_name in file_names:
                path = current / file_name
                if self._should_skip_file(path):
                    continue
                priority, reason = self._priority_for_file(path)
                if priority is None:
                    continue
                candidates.append((path, reason, priority))

        candidates.sort(key=lambda item: (item[2], len(item[0].relative_to(root).parts), _relative_posix(item[0], root)))
        return candidates

    def _should_skip_file(self, path: Path) -> bool:
        name = path.name.lower()
        suffix = path.suffix.lower()
        if name in SENSITIVE_FILE_NAMES or suffix in SENSITIVE_SUFFIXES:
            return True
        try:
            if path.stat().st_size > self.max_file_size_bytes:
                return True
        except OSError:
            return True
        return False

    def _priority_for_file(self, path: Path) -> Tuple[Optional[int], str]:
        name = path.name.lower()
        suffix = path.suffix.lower()
        if name in IMPORTANT_FILE_NAMES:
            return 0, "manifest/config with high deployment value"
        if name in ENTRYPOINT_NAMES or ".github/workflows" in _path_posix(path).lower():
            return 1, "likely application entrypoint or CI/CD config"
        if suffix in SOURCE_SUFFIXES:
            return 2, "source/config file"
        return None, ""

    def _read_text_file(self, path: Path) -> Optional[str]:
        try:
            raw = path.read_bytes()
        except OSError:
            return None
        if b"\x00" in raw[:2048]:
            return None
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="ignore")

    def _analyze_file(self, rel_path: str, content: str, state: "_DetectionState"):
        name = Path(rel_path).name.lower()
        lower = content.lower()

        if name == "package.json":
            self._analyze_package_json(rel_path, content, state)
        elif name == "requirements.txt":
            deps = _parse_requirements(content)
            state.dependencies[rel_path].update(deps)
            self._detect_python_deps(deps, state)
        elif name == "pyproject.toml":
            deps = _extract_words_from_dependency_text(content)
            state.dependencies[rel_path].update(deps)
            self._detect_python_deps(deps, state)
        elif name == "go.mod":
            deps = _parse_go_mod(content)
            state.dependencies[rel_path].update(deps)
            self._detect_go_deps(deps, state)
        elif name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
            state.stack.add("Docker")
            state.service_types.add("container")
            self._detect_database_words(lower, state)
        elif name in {"pnpm-lock.yaml", "yarn.lock", "package-lock.json"}:
            state.package_managers.add(_package_manager_from_lock(name))

        self._detect_source_patterns(rel_path, lower, state)

    def _analyze_package_json(self, rel_path: str, content: str, state: "_DetectionState"):
        try:
            package = json.loads(content)
        except json.JSONDecodeError:
            state.warnings.add(f"Could not parse {rel_path} as JSON.")
            return

        deps = {}
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            deps.update(package.get(key, {}) or {})
        dep_names = set(deps.keys())
        state.dependencies[rel_path].update(dep_names)
        state.runtimes.add("Node.js")

        if "packageManager" in package:
            state.package_managers.add(str(package["packageManager"]).split("@")[0])
        elif (Path(rel_path).parent / "pnpm-lock.yaml").name:
            scripts = package.get("scripts", {}) or {}
            if any("pnpm" in str(value) for value in scripts.values()):
                state.package_managers.add("pnpm")

        js_frameworks = {
            "next": ("Next.js", "frontend"),
            "react": ("React", "frontend"),
            "vue": ("Vue", "frontend"),
            "@angular/core": ("Angular", "frontend"),
            "svelte": ("Svelte", "frontend"),
            "@sveltejs/kit": ("SvelteKit", "frontend"),
            "vite": ("Vite", "frontend"),
            "express": ("Express", "backend"),
            "fastify": ("Fastify", "backend"),
            "@nestjs/core": ("NestJS", "backend"),
            "hono": ("Hono", "backend"),
        }
        for dep, (framework, layer) in js_frameworks.items():
            if dep in dep_names:
                state.stack.add(framework)
                state.frameworks[layer].add(framework)
                state.service_types.add(layer)

        db_deps = {
            "pg": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql2": "MySQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "mongoose": "MongoDB",
            "redis": "Redis",
            "ioredis": "Redis",
            "@prisma/client": "Prisma ORM",
            "prisma": "Prisma ORM",
            "drizzle-orm": "Drizzle ORM",
            "sequelize": "Sequelize ORM",
        }
        for dep, database in db_deps.items():
            if dep in dep_names:
                state.databases.add(database)
                state.service_types.add("database")

        scripts = package.get("scripts", {}) or {}
        script_values = " ".join(str(value).lower() for value in scripts.values())
        if "next" in script_values:
            state.stack.add("Next.js")
            state.frameworks["frontend"].add("Next.js")
            state.service_types.add("frontend")
        if any(cmd in script_values for cmd in ("node ", "tsx ", "ts-node", "nest ")):
            state.service_types.add("backend")

    def _detect_python_deps(self, deps: Iterable[str], state: "_DetectionState"):
        dep_set = {dep.lower() for dep in deps}
        state.runtimes.add("Python")
        py_frameworks = {
            "fastapi": ("FastAPI", "backend"),
            "django": ("Django", "backend"),
            "flask": ("Flask", "backend"),
            "litestar": ("Litestar", "backend"),
            "streamlit": ("Streamlit", "frontend"),
            "gradio": ("Gradio", "frontend"),
        }
        for dep, (framework, layer) in py_frameworks.items():
            if dep in dep_set:
                state.stack.add(framework)
                state.frameworks[layer].add(framework)
                state.service_types.add(layer)

        db_deps = {
            "psycopg2": "PostgreSQL",
            "psycopg2-binary": "PostgreSQL",
            "asyncpg": "PostgreSQL",
            "mysqlclient": "MySQL",
            "pymysql": "MySQL",
            "pymongo": "MongoDB",
            "redis": "Redis",
            "sqlalchemy": "SQLAlchemy ORM",
        }
        for dep, database in db_deps.items():
            if dep in dep_set:
                state.databases.add(database)
                state.service_types.add("database")

        ml_deps = {"torch", "tensorflow", "transformers", "sentence-transformers", "scikit-learn"}
        if dep_set & ml_deps:
            state.service_types.add("model")
            state.stack.add("AI/ML Python")

    def _detect_go_deps(self, deps: Iterable[str], state: "_DetectionState"):
        dep_text = " ".join(deps).lower()
        state.runtimes.add("Go")
        go_frameworks = {
            "github.com/gin-gonic/gin": "Gin",
            "github.com/gofiber/fiber": "Fiber",
            "github.com/labstack/echo": "Echo",
        }
        for dep, framework in go_frameworks.items():
            if dep in dep_text:
                state.stack.add(framework)
                state.frameworks["backend"].add(framework)
                state.service_types.add("backend")
        if any(db in dep_text for db in ("lib/pq", "pgx", "mysql", "mongo-driver", "redis")):
            self._detect_database_words(dep_text, state)

    def _detect_source_patterns(self, rel_path: str, lower: str, state: "_DetectionState"):
        suffix = Path(rel_path).suffix.lower()
        if suffix in {".py"}:
            if "fastapi(" in lower or "from fastapi" in lower:
                state.runtimes.add("Python")
                state.stack.add("FastAPI")
                state.frameworks["backend"].add("FastAPI")
                state.service_types.add("backend")
            if "flask(" in lower or "from flask" in lower:
                state.runtimes.add("Python")
                state.stack.add("Flask")
                state.frameworks["backend"].add("Flask")
                state.service_types.add("backend")
            if "django" in lower:
                state.runtimes.add("Python")
                state.stack.add("Django")
                state.frameworks["backend"].add("Django")
                state.service_types.add("backend")
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            if "from 'next" in lower or 'from "next' in lower or "/pages/api/" in rel_path.lower() or "/app/api/" in rel_path.lower():
                state.runtimes.add("Node.js")
                state.stack.add("Next.js")
                state.frameworks["frontend"].add("Next.js")
                state.service_types.add("frontend")
                if "/api/" in rel_path.lower():
                    state.service_types.add("backend")
            if "express()" in lower or "require('express')" in lower or 'require("express")' in lower:
                state.runtimes.add("Node.js")
                state.stack.add("Express")
                state.frameworks["backend"].add("Express")
                state.service_types.add("backend")
        elif suffix == ".go":
            if "package main" in lower:
                state.runtimes.add("Go")
                state.service_types.add("backend")

        self._detect_database_words(lower, state)

    def _detect_database_words(self, lower_text: str, state: "_DetectionState"):
        db_words = {
            "postgres": "PostgreSQL",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "mariadb": "MariaDB",
            "mongodb": "MongoDB",
            "mongo": "MongoDB",
            "redis": "Redis",
            "supabase": "Supabase",
            "sqlite": "SQLite",
        }
        for word, database in db_words.items():
            if re.search(rf"\b{re.escape(word)}\b", lower_text):
                state.databases.add(database)
                state.service_types.add("database")

    def _looks_like_entrypoint(self, rel_path: str, content: str) -> bool:
        name = Path(rel_path).name.lower()
        if name in ENTRYPOINT_NAMES:
            return True
        lower = content.lower()
        return any(pattern in lower for pattern in ("listen(", "fastapi(", "flask(", "package main", "createapp("))

    def _build_architecture_hints(self, state: "_DetectionState") -> List[str]:
        hints: List[str] = []
        if "backend" in state.service_types:
            hints.append("Backend/server runtime detected; avoid recommending pure static hosting as the only deployment target.")
        if "frontend" in state.service_types and "backend" in state.service_types:
            hints.append("Frontend and backend capabilities detected; consider split services or a platform that supports server rendering/API routes.")
        if "database" in state.service_types:
            hints.append("Database dependency detected; recommend managed database or explicit database service provisioning.")
        if "container" in state.service_types:
            hints.append("Docker/compose config detected; container deployment is likely compatible.")
        if "model" in state.service_types:
            hints.append("AI/ML dependency detected; check memory/CPU/GPU needs before choosing free-tier deployment.")
        if not hints:
            hints.append("No server/database signals found; static or serverless deployment may be suitable if build output is static.")
        return hints


@dataclass
class _DetectionState:
    stack: Set[str] = field(default_factory=set)
    service_types: Set[str] = field(default_factory=set)
    runtimes: Set[str] = field(default_factory=set)
    frameworks: Dict[str, Set[str]] = field(default_factory=lambda: {"frontend": set(), "backend": set(), "model": set()})
    databases: Set[str] = field(default_factory=set)
    package_managers: Set[str] = field(default_factory=set)
    dependencies: Dict[str, Set[str]] = field(default_factory=lambda: {})
    warnings: Set[str] = field(default_factory=set)
    file_count: int = 0

    def __post_init__(self):
        self.dependencies = _DefaultSetDict()


class _DefaultSetDict(dict):
    def __missing__(self, key):
        self[key] = set()
        return self[key]


def analyze_repository(
    repo_url: Optional[str] = None,
    repo_path: Optional[str] = None,
    max_files: int = DEFAULT_MAX_FILES,
    max_snippets: int = DEFAULT_MAX_SNIPPETS,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> RepositoryProfile:
    if repo_url and repo_path:
        raise RepositoryAnalysisError("Use either repo_url or repo_path, not both.")
    if not repo_url and not repo_path:
        raise RepositoryAnalysisError("Repository URL or path is required.")

    analyzer = RepositoryAnalyzer(
        max_files=max_files,
        max_snippets=max_snippets,
        max_file_size_bytes=max_file_size_bytes,
    )

    if repo_path:
        return analyzer.analyze_path(repo_path, source=str(Path(repo_path).expanduser().resolve()))

    with tempfile.TemporaryDirectory(prefix="deploybuddy-repo-") as tmp_dir:
        clone_dir = Path(tmp_dir) / "repo"
        _clone_public_repo(repo_url, clone_dir)
        return analyzer.analyze_path(str(clone_dir), source=repo_url)


def _clone_public_repo(repo_url: str, clone_dir: Path):
    if not shutil.which("git"):
        raise RepositoryAnalysisError("git executable not found; cannot clone repo URL.")
    cmd = ["git", "clone", "--depth", "1", repo_url, str(clone_dir)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RepositoryAnalysisError(f"Failed to clone repository: {detail}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RepositoryAnalysisError("Timed out while cloning repository.") from exc


def _parse_requirements(content: str) -> Set[str]:
    deps = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        dep = re.split(r"[<>=~!\[]", line, maxsplit=1)[0].strip()
        if dep:
            deps.add(dep.lower())
    return deps


def _parse_go_mod(content: str) -> Set[str]:
    deps = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line in {"require (", ")"}:
            continue
        if line.startswith("module "):
            deps.add(line.split(" ", 1)[1].strip())
        elif line.startswith("require "):
            deps.add(line.split()[1])
        elif "/" in line:
            deps.add(line.split()[0])
    return deps


def _extract_words_from_dependency_text(content: str) -> Set[str]:
    known = {
        "fastapi",
        "django",
        "flask",
        "litestar",
        "streamlit",
        "gradio",
        "psycopg2",
        "psycopg2-binary",
        "asyncpg",
        "mysqlclient",
        "pymysql",
        "pymongo",
        "redis",
        "sqlalchemy",
        "torch",
        "tensorflow",
        "transformers",
        "sentence-transformers",
        "scikit-learn",
    }
    lower = content.lower()
    return {name for name in known if re.search(rf"\b{re.escape(name)}\b", lower)}


def _package_manager_from_lock(name: str) -> str:
    if name == "pnpm-lock.yaml":
        return "pnpm"
    if name == "yarn.lock":
        return "yarn"
    if name == "package-lock.json":
        return "npm"
    return name


def _language_for_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".py": "python",
        ".go": "go",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
    }.get(suffix, "")


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _path_posix(path: Path) -> str:
    return path.as_posix()
