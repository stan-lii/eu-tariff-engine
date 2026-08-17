#!/usr/bin/env python3
"""Scaffold a new module or adapter from the canonical template.

Usage:
    python scripts/new_module.py domain measure "Tariff measure domain models"
    python scripts/new_module.py adapters taric "TARIC XML source adapter" --adapter

This script creates the directory structure defined in Part A2 of the build plan.
Every new package is created from templates/module/ and optionally includes
adapter-specific files (client.py, mapper.py, fixtures/).
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src" / "tariff_engine"
MODULE_TEMPLATE_DIR = PROJECT_ROOT / "templates" / "module"
ADAPTER_TEMPLATE_DIR = PROJECT_ROOT / "templates" / "adapter"

# Files every module gets (from Part A2)
MODULE_FILES = [
    "__init__.py",
    "models.py",
    "ports.py",
    "service.py",
    "errors.py",
    "README.md",
]

# Extra files adapters get (from Part A2)
ADAPTER_FILES = [
    "client.py",
    "mapper.py",
]


def render_template(template_path: Path, replacements: dict[str, str]) -> str:
    """Read a template file and replace all placeholders."""
    content = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def scaffold_module(
    layer: str,
    name: str,
    description: str,
    is_adapter: bool,
) -> None:
    """Create a new module directory with all required files."""
    target_dir = SRC_ROOT / layer / name

    if target_dir.exists():
        print(f"ERROR: {target_dir} already exists. Aborting.")
        sys.exit(1)

    replacements = {
        "{{MODULE_NAME}}": name,
        "{{MODULE_DESCRIPTION}}": description,
    }

    # Create the directory
    target_dir.mkdir(parents=True)
    print(f"Created {target_dir}/")

    # Create standard module files
    for filename in MODULE_FILES:
        template_file = MODULE_TEMPLATE_DIR / f"{filename}.template"
        if template_file.exists():
            content = render_template(template_file, replacements)
        else:
            # Fallback if template missing
            content = f'"""{description}."""\n'

        target_file = target_dir / filename
        target_file.write_text(content, encoding="utf-8")
        print(f"  Created {filename}")

    # Create adapter-specific files
    if is_adapter:
        for filename in ADAPTER_FILES:
            template_file = ADAPTER_TEMPLATE_DIR / f"{filename}.template"
            if template_file.exists():
                content = render_template(template_file, replacements)
            else:
                content = f'"""{description}."""\n'

            target_file = target_dir / filename
            target_file.write_text(content, encoding="utf-8")
            print(f"  Created {filename}")

        # Create fixtures directory
        fixtures_dir = target_dir / "fixtures"
        fixtures_dir.mkdir()
        (fixtures_dir / ".gitkeep").touch()
        print("  Created fixtures/")

    # Create matching test directory
    test_dir = PROJECT_ROOT / "tests" / "unit" / "tariff_engine" / layer / name
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "__init__.py").write_text("", encoding="utf-8")

    test_file = test_dir / f"test_{name}.py"
    test_content = f'"""Tests for tariff_engine.{layer}.{name}."""\n'
    test_file.write_text(test_content, encoding="utf-8")
    print(f"  Created tests/unit/tariff_engine/{layer}/{name}/test_{name}.py")

    print(f"\nDone. Module scaffolded at {target_dir}")
    print("Next: run 'make check' to verify it passes all gates.")


def main() -> None:
    """Parse arguments and scaffold the module."""
    parser = argparse.ArgumentParser(
        description="Scaffold a new module from the canonical template.",
    )
    parser.add_argument(
        "layer",
        choices=["domain", "application", "adapters", "interfaces"],
        help="Which layer the module belongs to.",
    )
    parser.add_argument(
        "name",
        help="Module name in snake_case (e.g. 'measure', 'taric').",
    )
    parser.add_argument(
        "description",
        help="One-line description of the module.",
    )
    parser.add_argument(
        "--adapter",
        action="store_true",
        help="Include adapter-specific files (client.py, mapper.py, fixtures/).",
    )

    args = parser.parse_args()
    scaffold_module(args.layer, args.name, args.description, args.adapter)


if __name__ == "__main__":
    main()
