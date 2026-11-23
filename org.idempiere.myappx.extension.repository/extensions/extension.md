# Folder Structure

Active catalog source only. Must match `extensions.list` 1:1.
Remove a directory from `extensions/` when it leaves the list.

```Text
com.example.extension.name/
├── info.md
├── CHANGELOG.md
├── assets/
│   └── screenshot.png
└── 1.0.0/
    └── metadata.json
```
- Root is extension name
- info.md: Human-readable description
- CHANGELOG.md: Change log
- assets: Static assets (image, csv, etc)
- 1.0.0: The single current version folder
- metadata.json: Technical metadata & bundle links
