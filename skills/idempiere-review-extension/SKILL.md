---
name: idempiere-review-extension
description: Reviews an iDempiere extension folder for info.md, metadata.json formatting and content, and verifies 2Pack archives in downloaded jar files.
---

# iDempiere Extension Review

This skill guides you through reviewing an iDempiere extension folder to ensure it complies with the standard extension specification.

## Prerequisites
- A extension folder containing `info.md` and a version-specific sub-directory with `metadata.json`.

## Review Steps

### 1. `info.md` Review
- **Formatting and Sections**: Verify that `info.md` strictly contains the following sections as outlined in the extension specification:
  - Summary
  - Features
  - Compatibility
  - Database Changes (if any)
  - Usage & Configuration
  - Author/Support
- **Content Check**: Review the text content for any grammar, wording, and semantic issues. Correct or suggest improvements as necessary.
- **Broken Link**: Verify no broken links.

### 2. `metadata.json` Review
- **Content and Formatting**: Verify that `metadata.json` conforms to the specified schema (`schema.json`).
- Ensure all required properties (`id`, `version`, `idempiereVersion`, `bundles`, `entityType`) are present and properly formatted according to their patterns (e.g., semantic version format for `version`, valid URI for `downloadUrl`, etc.).

### 3. Jar File and 2Pack Verification
For each bundle listed in the `bundles` array of `metadata.json`, perform the following:

1. **Download the Jar**: Download the jar file from the specified `downloadUrl`.
   - **Version Check**: Verify that the version of the jar file matches the version specified in `metadata.json`.
   - **Hash Check**: Verify that the hash of the jar file matches the hash specified in `metadata.json`.
2. **Extract Jar**: Unzip the jar file to inspect its contents, specifically the `META-INF` folder.
3. **Verify 2Pack Archives**:
   - Check the 2Pack files located inside the `META-INF` folder.
   - **Naming Convention**: Verify that the 2Pack archive follows the exact naming convention: `2Pack_{$version}` (where `{$version}` matches the extension version in `metadata.json`).
   - **Entity Type**: Verify that the 2Pack `entityType` matches the `entityType` specified in `metadata.json`.
   - **Grammar & Semantics**: Review the contents of the 2Pack XML file(s) to verify any grammar, wording, and semantic issues in the XML data.
   - **Tenant Check**: Verify that the 2Pack is created for System tenant.
4. **Collect SQL Statements**:
   - Scan the 2Pack XML files for any SQL statements.
   - If any SQL statements exist, collect all of them into a file named `ExtensionSQLStatements.sql` in the root of the extension folder.
   - For each extracted SQL statement, the format MUST be exactly:
     ```
     {source 2pack file}/{line no}:
     {sql statement}
     
     ```
     *(Ensure there is a Unix newline (`\n`) after the colon, and another newline after the statement).*

## Execution Notes
- You can use standard bash commands (like `wget`, `curl`, `unzip`) for downloading and extraction.
- To find line numbers and extract SQL statements from the XML, write a short parsing script (e.g., in Python or using `grep -n` and `sed`) to reliably format the output according to the requirements.
