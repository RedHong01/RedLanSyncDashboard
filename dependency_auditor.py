#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import re
import shutil
import time

from project_packager import DEFAULT_EXCLUDES, is_excluded, rel_posix


ADOBE_PROJECT_EXTENSIONS = {
    ".aep": "After Effects",
    ".aepx": "After Effects",
    ".prproj": "Premiere Pro",
    ".mogrt": "Motion Graphics Template",
    ".psd": "Photoshop",
    ".psb": "Photoshop",
    ".ai": "Illustrator",
    ".ait": "Illustrator",
    ".indd": "InDesign",
    ".idml": "InDesign",
    ".xd": "Adobe XD",
    ".fla": "Animate",
    ".animate": "Animate",
}

FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".dfont", ".woff", ".woff2"}

ADOBE_PROJECT_ASSET_EXTENSIONS = {
    ".aex",
    ".ffx",
    ".jsx",
    ".jsxbin",
    ".mogrt",
    ".plugin",
    ".zxp",
}

TEXT_SCAN_EXTENSIONS = {
    ".aepx",
    ".prproj",
    ".idml",
    ".xml",
    ".json",
    ".jsx",
    ".txt",
    ".css",
    ".html",
    ".svg",
}

FONT_PATTERNS = [
    re.compile(r"font(?:Family|Name|PostScriptName)?[\"'\s:=]+([A-Za-z0-9][^\"'<>{}\r\n]{1,80})", re.IGNORECASE),
    re.compile(r"font-family\s*:\s*([^;{}\r\n]{1,120})", re.IGNORECASE),
    re.compile(r"Typeface[\"'\s:=]+([A-Za-z0-9][^\"'<>{}\r\n]{1,80})", re.IGNORECASE),
]

PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\[^\"'<>\r\n]+"),
    re.compile(r"/(?:Users|Volumes|Library|Applications)/[^\"'<>\r\n]+"),
    re.compile(r"\\\\[^\"'<>\r\n]+"),
]


def now_stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def safe_rel(path: Path, root: Path) -> str:
    try:
        return rel_posix(path.relative_to(root))
    except ValueError:
        return str(path)


def normalized_name(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value).casefold()


def display_name_from_font(path: Path) -> str:
    name = path.stem
    for suffix in ("-Regular", "_Regular", " Regular", "-Bold", "_Bold", " Bold"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.replace("_", " ").replace("-", " ").strip() or path.stem


def walk_project(source: Path, excludes: list[str]):
    for current, dirs, files in os.walk(source):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if not is_excluded(name, excludes) and name != "_DependencyBundle"]
        for name in files:
            if is_excluded(name, excludes):
                continue
            yield current_path / name


def decode_text_sample(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        raw = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding, errors="ignore")
        except UnicodeError:
            continue
    return ""


def extract_font_references(text: str) -> list[str]:
    found = []
    for pattern in FONT_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1).strip().strip("'\"")
            value = re.sub(r"[,;].*$", "", value).strip()
            if value and len(value) <= 120 and value.casefold() not in {"font", "family", "name"}:
                found.append(value)
    return sorted(set(found), key=str.casefold)


def extract_external_paths(text: str) -> list[str]:
    found = []
    for pattern in PATH_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).strip().strip("'\"")
            if len(value) <= 500:
                found.append(value)
    return sorted(set(found), key=str.casefold)


def font_roots(system: str | None = None) -> list[Path]:
    system = system or platform.system()
    home = Path.home()
    if system == "Windows":
        roots = [
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
            Path(os.environ.get("LOCALAPPDATA", str(home / "AppData/Local"))) / "Microsoft/Windows/Fonts",
        ]
    elif system == "Darwin":
        roots = [
            home / "Library/Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
        ]
    else:
        roots = [
            home / ".local/share/fonts",
            Path("/usr/local/share/fonts"),
            Path("/usr/share/fonts"),
        ]
    return [root for root in roots if root.exists()]


def scan_installed_fonts(limit: int = 5000) -> list[dict]:
    fonts = []
    seen = set()
    for root in font_roots():
        for current, _dirs, files in os.walk(root):
            for name in files:
                path = Path(current) / name
                if path.suffix.lower() not in FONT_EXTENSIONS:
                    continue
                key = str(path).casefold()
                if key in seen:
                    continue
                seen.add(key)
                fonts.append(
                    {
                        "name": display_name_from_font(path),
                        "file": path.name,
                        "path": str(path),
                        "extension": path.suffix.lower(),
                    }
                )
                if len(fonts) >= limit:
                    return fonts
    return sorted(fonts, key=lambda item: item["name"].casefold())


def adobe_plugin_roots(system: str | None = None) -> list[Path]:
    system = system or platform.system()
    home = Path.home()
    roots = []
    if system == "Windows":
        program_files = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]
        for base in [Path(value) for value in program_files if value]:
            roots.extend(
                [
                    base / "Adobe/Common/Plug-ins/7.0/MediaCore",
                    base / "Common Files/Adobe/Plug-Ins/CC",
                ]
            )
            roots.extend(base.glob("Adobe/Adobe After Effects*/Support Files/Plug-ins"))
            roots.extend(base.glob("Adobe/Adobe Photoshop*/Plug-ins"))
            roots.extend(base.glob("Adobe/Adobe Premiere Pro*/Plug-ins"))
        appdata = Path(os.environ.get("APPDATA", str(home / "AppData/Roaming")))
        localappdata = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData/Local")))
        roots.extend([appdata / "Adobe/Common/Plug-ins", localappdata / "Adobe/Common/Plug-ins"])
    elif system == "Darwin":
        roots.extend(
            [
                Path("/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"),
                Path("/Library/Application Support/Adobe/Plug-Ins/CC"),
                home / "Library/Application Support/Adobe/Common/Plug-ins",
            ]
        )
        roots.extend(Path("/Applications").glob("Adobe After Effects*/Plug-ins"))
        roots.extend(Path("/Applications").glob("Adobe Photoshop*/Plug-ins"))
        roots.extend(Path("/Applications").glob("Adobe Premiere Pro*/Plug-ins"))
    return [root for root in roots if root.exists()]


def scan_adobe_plugins(limit: int = 1000) -> list[dict]:
    plugins = []
    seen = set()
    for root in adobe_plugin_roots():
        try:
            children = sorted(root.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            continue
        for child in children:
            key = str(child).casefold()
            if key in seen:
                continue
            seen.add(key)
            plugins.append(
                {
                    "name": child.stem if child.is_file() else child.name,
                    "path": str(child),
                    "root": str(root),
                    "type": "folder" if child.is_dir() else "file",
                    "extension": child.suffix.lower(),
                }
            )
            if len(plugins) >= limit:
                return plugins
    return plugins


def scan_adobe_apps() -> list[dict]:
    apps = []
    system = platform.system()
    if system == "Windows":
        program_files = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]
        for base in [Path(value) for value in program_files if value]:
            for path in base.glob("Adobe/Adobe *"):
                if path.is_dir():
                    apps.append({"name": path.name, "path": str(path)})
    elif system == "Darwin":
        for path in Path("/Applications").glob("Adobe *"):
            if path.is_dir():
                apps.append({"name": path.name, "path": str(path)})
    return sorted(apps, key=lambda item: item["name"].casefold())


def endpoint_inventory() -> dict:
    return {
        "hostname": platform.node(),
        "platform": platform.system(),
        "timestamp": now_stamp(),
        "fonts": scan_installed_fonts(),
        "adobe_plugins": scan_adobe_plugins(),
        "adobe_apps": scan_adobe_apps(),
    }


def copy_unique(src: Path, dest_dir: Path, used_names: set[str]) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / src.name
    if target.name.casefold() in used_names or target.exists():
        target = dest_dir / "{}_{}{}".format(src.stem, abs(hash(str(src))) % 1_000_000, src.suffix)
    shutil.copy2(src, target)
    used_names.add(target.name.casefold())
    return target


def package_dependencies(source: Path, result: dict, bundle_dir: Path) -> dict:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    copied = {"fonts": [], "project_assets": []}
    used_font_names: set[str] = set()
    used_asset_names: set[str] = set()

    for item in result["project_fonts"]:
        copied_path = copy_unique(source / item["relative_path"], bundle_dir / "Fonts/Project", used_font_names)
        copied["fonts"].append(str(copied_path))

    for item in result["project_adobe_assets"]:
        copied_path = copy_unique(source / item["relative_path"], bundle_dir / "AdobeProjectAssets", used_asset_names)
        copied["project_assets"].append(str(copied_path))

    for font_ref in result["font_references"]:
        matched = font_ref.get("local_match")
        if not matched:
            continue
        font_path = Path(matched.get("path", ""))
        if font_path.exists():
            copied_path = copy_unique(font_path, bundle_dir / "Fonts/ReferencedInstalled", used_font_names)
            copied["fonts"].append(str(copied_path))

    manifest_path = bundle_dir / "dependency_manifest.json"
    manifest = dict(result)
    manifest["bundle"] = {
        "path": str(bundle_dir),
        "copied": copied,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (bundle_dir / "README_DEPENDENCIES.md").write_text(dependency_markdown(manifest), encoding="utf-8")
    return {"path": str(bundle_dir), "manifest": str(manifest_path), "copied": copied}


def dependency_markdown(result: dict) -> str:
    lines = [
        "# Project Dependency Bundle",
        "",
        "Generated: {}".format(result.get("generated_at", "")),
        "Source: `{}`".format(result.get("source", "")),
        "",
        "## Adobe Project Files",
    ]
    if result["adobe_files"]:
        lines.extend("- `{relative_path}` ({application})".format(**item) for item in result["adobe_files"][:200])
    else:
        lines.append("- None detected")
    lines.extend(["", "## Font References"])
    if result["font_references"]:
        for item in result["font_references"][:200]:
            status = "local match: {}".format(item["local_match"]["file"]) if item.get("local_match") else "no local file match"
            lines.append("- `{}` ({})".format(item["name"], status))
    else:
        lines.append("- None detected in text-readable project files")
    lines.extend(
        [
            "",
            "## Notes",
            "- Fonts and Adobe plugins may be licensed; verify rights before installing on another computer.",
            "- Adobe plugins are usually platform/version specific. This bundle records plugin state and copies project-local assets, but it does not install third-party plugins automatically.",
        ]
    )
    return "\n".join(lines) + "\n"


def match_font_reference(name: str, installed_fonts: list[dict]) -> dict | None:
    target = normalized_name(name)
    for font in installed_fonts:
        candidates = [font.get("name", ""), Path(font.get("file", "")).stem]
        if any(normalized_name(candidate) == target for candidate in candidates):
            return font
    for font in installed_fonts:
        if target and target in normalized_name(font.get("name", "")):
            return font
    return None


def compare_remote(result: dict, remote_inventory: dict | None) -> dict:
    if not remote_inventory:
        return {"available": False, "missing_fonts": [], "missing_plugins": []}
    remote_fonts = remote_inventory.get("fonts", [])
    remote_plugins = remote_inventory.get("adobe_plugins", [])
    missing_fonts = []
    for item in result["font_references"]:
        if not match_font_reference(item["name"], remote_fonts):
            missing_fonts.append(item)
    remote_plugin_names = {normalized_name(item.get("name", "")) for item in remote_plugins}
    missing_plugins = [
        item
        for item in result["project_adobe_assets"]
        if item["extension"] in {".aex", ".plugin", ".zxp"} and normalized_name(Path(item["relative_path"]).stem) not in remote_plugin_names
    ]
    return {
        "available": True,
        "remote_hostname": remote_inventory.get("hostname", ""),
        "remote_platform": remote_inventory.get("platform", ""),
        "missing_fonts": missing_fonts,
        "missing_plugins": missing_plugins,
    }


def audit_project_dependencies(
    source: Path,
    *,
    excludes: list[str] | None = None,
    package: bool = False,
    bundle_dir: Path | None = None,
    remote_inventory: dict | None = None,
) -> dict:
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise ValueError("Source folder does not exist")
    excludes = (excludes or DEFAULT_EXCLUDES) + ["_DependencyBundle", "_CrossPlatformReport"]
    installed_fonts = scan_installed_fonts()
    installed_plugins = scan_adobe_plugins()
    adobe_apps = scan_adobe_apps()
    font_refs = set()
    external_paths = set()
    text_reference_files = []
    adobe_files = []
    project_fonts = []
    project_adobe_assets = []
    total_files = 0

    for path in walk_project(source, excludes):
        total_files += 1
        suffix = path.suffix.lower()
        rel = safe_rel(path, source)
        if suffix in ADOBE_PROJECT_EXTENSIONS:
            adobe_files.append({"relative_path": rel, "application": ADOBE_PROJECT_EXTENSIONS[suffix], "extension": suffix})
        if suffix in FONT_EXTENSIONS:
            project_fonts.append({"relative_path": rel, "name": display_name_from_font(path), "extension": suffix})
        if suffix in ADOBE_PROJECT_ASSET_EXTENSIONS:
            project_adobe_assets.append({"relative_path": rel, "extension": suffix})
        if suffix in TEXT_SCAN_EXTENSIONS:
            text = decode_text_sample(path)
            fonts = extract_font_references(text)
            paths = extract_external_paths(text)
            if fonts or paths:
                text_reference_files.append({"relative_path": rel, "font_references": fonts, "external_paths": paths})
                font_refs.update(fonts)
                external_paths.update(paths)

    font_references = [
        {"name": name, "local_match": match_font_reference(name, installed_fonts)}
        for name in sorted(font_refs, key=str.casefold)
    ]
    result = {
        "source": str(source),
        "generated_at": now_stamp(),
        "host": {"hostname": platform.node(), "platform": platform.system()},
        "summary": {
            "total_files": total_files,
            "adobe_file_count": len(adobe_files),
            "project_font_count": len(project_fonts),
            "font_reference_count": len(font_references),
            "external_reference_count": len(external_paths),
            "project_adobe_asset_count": len(project_adobe_assets),
            "installed_font_count": len(installed_fonts),
            "installed_adobe_plugin_count": len(installed_plugins),
            "adobe_dependency_review_required": bool(adobe_files),
        },
        "categories": [
            "adobe_project_files" if adobe_files else "",
            "fonts" if project_fonts or font_references else "",
            "adobe_plugins_and_presets" if project_adobe_assets or adobe_files else "",
            "external_paths" if external_paths else "",
        ],
        "adobe_files": adobe_files[:500],
        "project_fonts": project_fonts[:500],
        "font_references": font_references[:500],
        "project_adobe_assets": project_adobe_assets[:500],
        "external_paths": sorted(external_paths, key=str.casefold)[:500],
        "text_reference_files": text_reference_files[:500],
        "installed": {
            "fonts_sample": installed_fonts[:200],
            "adobe_plugins_sample": installed_plugins[:200],
            "adobe_apps": adobe_apps,
        },
        "remote_comparison": {},
        "bundle": {},
        "warnings": [
            "Binary Adobe files can hide font/plugin usage. Open the project in the Adobe app and save text interchange formats when deeper extraction is needed.",
            "Fonts and plugins may be licensed or platform-specific; the dashboard packages manifests and project-local assets, but does not auto-install them.",
        ],
    }
    result["categories"] = [item for item in result["categories"] if item]
    result["remote_comparison"] = compare_remote(result, remote_inventory)
    if package:
        result["bundle"] = package_dependencies(source, result, bundle_dir or (source / "_DependencyBundle"))
    return result
