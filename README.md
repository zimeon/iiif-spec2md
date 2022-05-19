# ocfl-spec2md

## Goal

Take OCFL specification and implementation notes documents and transform from XML for ReSpec to Markdown with similar structure and look. Use [IIIF Image API](https://raw.githubusercontent.com/IIIF/api/main/source/image/3.0/index.md) as the model for Markdown format. Fixes [https://github.com/OCFL/spec/issues/554].

## Outputs

These are being written to a copy of <https://github.com/zimeon/ocfl-spec2md> and github pages versions are hosted at:

* [Spec](https://zimeon.github.io/ocfl-spec/draft/spec/) from [current draft](https://ocfl.io/draft/spec/)
* [Implementation Notes](https://zimeon.github.io/ocfl-spec/draft/implementation-notes/) from [current draft](https://ocfl.io/draft/implementation-notes/)

## Misc Notes

The OCFL site, <https://ocfl.io/>, is a github pages site. The settings are from branch `main`, based at the repository root, no theme is set in the repository settings.

This script relies on having a fork of the [OCFL spec](https://github.com/OCFL/spec) repository checked out at `../ocfl-spec` for the input, and `../ocfl-spec-md` for the output.
