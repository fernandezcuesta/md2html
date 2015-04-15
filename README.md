# md2html
Python Markdown to HTML convertor

**usage**: md2html.py [-h] [-C CSS_FILE [CSS_FILE ...]] [-T HTML_TEMPLATE]
                  [-F FAVICON] [-B BACKGROUND_IMG] [-L LOGO]
                  [-M MARKDOWN_EXTENSION [MARKDOWN_EXTENSION ...]]
                  [-O OUTPUT_FILE]
                  input_file

positional arguments:
  input_file            *Markdown input file*

optional arguments:
  -h, --help            *show this help message and exit*
  -C CSS_FILE [CSS_FILE ...], --css CSS_FILE [CSS_FILE ...]
                        *CSS files*
  -T HTML_TEMPLATE, --template HTML_TEMPLATE
                        *HTML template for Jinja2*
  -F FAVICON, --favicon FAVICON
                        *PNG/BMP/JPG favicon*
  -B BACKGROUND_IMG, --background BACKGROUND_IMG
                        *PNG/BMP/JPG background image*
  -L LOGO, --logo LOGO  Logo image (PNG/BMP/JPG)
  -M MARKDOWN_EXTENSION [MARKDOWN_EXTENSION ...], --extensions MARKDOWN_EXTENSION [MARKDOWN_EXTENSION ...]
                        *Extensions from markdown module, defaults to
*
  -O OUTPUT_FILE, --output_file OUTPUT_FILE
                        *HTML output file, defaults to **stdout***


- **Additional CSS styles can be defined in the markdown file metadata**
- **Logo, favicon and background images can be set directly in the markdown **
- Any setting passed via CLI overrides these in the markdown, except for CSS (all are applied)


[TODO]

* Allow setting a list of templates directly in the markdown file
* Allow both single-file HTML and multiple files (do not embed CSS or images)
* Conversion to other formats
* Global speedup