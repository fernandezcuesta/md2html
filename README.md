# md2html
**Python Markdown to single-file HTML convertor**

```
usage: md2html.py [-h] [-C CSS_FILE [CSS_FILE ...]] [-W BASE_FOLDER]
                  [-T HTML_TEMPLATE] [-F FAVICON] [-B BACKGROUND_IMG]
                  [-L LOGO] [-M MARKDOWN_EXTENSION [MARKDOWN_EXTENSION ...]]
                  [-O OUTPUT_FILE]
                  input_file

positional arguments:
  input_file            Markdown input file

optional arguments:
  -h, --help            show this help message and exit
  -C CSS_FILE [CSS_FILE ...], --css CSS_FILE [CSS_FILE ...]
                        CSS files
  -W BASE_FOLDER, --working-dir BASE_FOLDER
                        Working base directory where /css and /layout folders are found
  -T HTML_TEMPLATE, --template HTML_TEMPLATE
                        HTML template for Jinja2, defaults to template.html
  -F FAVICON, --favicon FAVICON
                        PNG/BMP/JPG favicon
  -B BACKGROUND_IMG, --background BACKGROUND_IMG
                        PNG/BMP/JPG background image
  -L LOGO, --logo LOGO  Logo image (PNG/BMP/JPG)
  -M MARKDOWN_EXTENSION [MARKDOWN_EXTENSION ...], --extensions MARKDOWN_EXTENSION [MARKDOWN_EXTENSION ...]
                        Extensions from markdown module, defaults to ['codehilite', 'tables', "toc(marker='')", 'meta']
  -O OUTPUT_FILE, --output_file OUTPUT_FILE
                        HTML output file, defaults to stdout

```

- **Additional CSS styles can be defined in the markdown file metadata**
    - It is assumed they're located in `/css` subfolder
- **Base HTML template** can be set, defaults to `template.html`
- **Logo, favicon and background images can be set directly in the markdown**
- Any setting passed via CLI overrides these in the markdown, except for CSS (all are applied)

## Recognized metadata in markdown file:

- **date**: Document's creation date. If omitted, current date is shown instead

## Recognized by default template file:

- **Title**: Document's title/s
- **css**: name of the CSS files under `/css` subfolder
- **template**: name of the base template under `/layout` subfolder
- **Author**: Author/s of the document
- **email**: email addresses for each author
- **logo**: file or URL for the optional logo image
- **logolink**: valid URL for the logo
- **theme**: anything here will be passed as: `<body class="{{ }}">`
- **background_img**: background image
- **favicon**: favicon file (not .ico)

## [TODO]

* ~~Let CSS and templates being in any location~~
* ~~Allow setting a list of templates directly in the markdown file~~ moved most part of the logic to the templates
* Allow both HTML-embedded and online HTML (do not embed CSS or images for online resources)
* Fix TOC to allow pandoc's-like `--toc-depth`
* Conversion to other formats
* ~~Global speedup, refactoring, ...~~
* ~~Check if logolink contains a valid URL~~ moved extra logic to templates
* Complete refactoring
