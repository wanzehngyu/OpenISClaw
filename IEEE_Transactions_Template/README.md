# IEEE Transactions-style LaTeX Template

This package was revised from the uploaded IEEE Access template to better match the supplied English reference paper.

Main changes:

1. The main class is now `IEEEtran.cls` with `journal,twoside` options.
2. The title is black and no longer uses the IEEE Access blue title block.
3. The abstract and index terms are placed after `\maketitle`, so they appear inside the two-column text flow.
4. The IEEE Access masthead, logo, and header have been removed.
5. The top running header is controlled by `\markboth{...}{...}` and can be edited directly.
6. `\PARstart` is aliased to `\IEEEPARstart` for compatibility with text migrated from the IEEE Access template.

Compile on Overleaf:

- Upload the whole folder or the zip package.
- Set `access.tex` or `main.tex` as the main file.
- Compiler: pdfLaTeX.

Compile locally:

```bash
latexmk -pdf access.tex
```

If local compilation fails, make sure these standard packages/classes are available: `IEEEtran.cls`, `IEEEtran.bst`, `cite`, `amsmath`, `amssymb`, `graphicx`, `xcolor`, `hyperref`, `url`, and `algorithmic`. They are included in most TeX Live / MiKTeX installations and on Overleaf. `IEEEtran.cls` and `IEEEtran.bst` are included in this package to reduce local dependency issues.
