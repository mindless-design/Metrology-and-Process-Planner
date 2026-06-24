# KLayout Package Guidelines

This project follows KLayout's official Salt package model.

Sources:

- [About Packages](https://www.klayout.de/doc/about/packages.html)
- [About Macro Development](https://www.klayout.de/doc/about/macro_editor.html)
- [The Package Cookbook](https://www.klayout.de/package_cookbook.html)
- [Salt.Mine Package Index](https://sami.klayout.org/)

## Official Package Model

KLayout's package manager is called Salt. A package can provide Python or Ruby
macros, DRC runsets, technologies, fonts, static libraries, PCells, code
libraries, or binary extensions.

KLayout identifies packages by name. Package names must be unique in the package
universe. Official docs recommend prefixed names such as
`www.mydomain.org/nameofpackage` when publishing broadly.

Package metadata lives in `grain.xml` at the package root. KLayout expects this
file at the root of the package file hierarchy. Salt package metadata should
include at least a version, title, description, author/contact information,
license, and documentation link.

KLayout can create packages from templates through:

```text
Tools -> Manage Packages -> Current Packages -> Create (Edit) Package
```

The generated package appears under KLayout's `salt` folder and can then be put
under version control.

## Macro And Library Folders

KLayout scans macro repositories recursively. Python macros should live in a
`pymacros` folder. Plain Python libraries can live in a sibling `python` folder;
KLayout adds that folder to Python's import path.

This project uses:

```text
grain.xml
pymacros/
  metrology_process_planner_bootstrap.py
python/
  metrology_process_planner/
```

The bootstrap macro is the thin KLayout-discovered entrypoint. The importable
library remains normal Python code inside `python/metrology_process_planner`.

## Deployment Notes

KLayout package URLs can point to a hierarchy whose root contains `grain.xml`.
The package docs describe WebDAV/Subversion URLs and Git URLs with the `git+`
prefix. The current docs also note that the older GitHub Subversion-bridge
cookbook path is outdated, so public GitHub deployment should be rechecked near
release time.

For local organization deployment, KLayout can use a custom package index via
the `KLAYOUT_SALT_MINE` environment variable. The index is XML and can be served
over HTTP, HTTPS, or a file URL.

## Project Rules

- Keep `grain.xml` at repository root.
- Keep KLayout-discovered macros under root `pymacros`.
- Keep importable plugin code under root `python`.
- Do not put core domain logic in `pymacros`.
- Keep KLayout/Qt integration thin and inside `infrastructure/klayout` or `ui`.
- Treat `pymacros` as bootstrapping glue only.

