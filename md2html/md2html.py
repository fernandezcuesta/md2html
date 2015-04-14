#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:18:42 2015

@author: fernandezjm
"""

import jinja2
import markdown
import os
import re
import argparse
import sys
import imghdr
from cStringIO import StringIO
from rfc3987 import parse
from urllib2 import urlopen
from csscompressor import compress
from datetime import date

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_TEMPLATE = 'layout/template.html'
MD_EXTENSIONS = ['codehilite', 'tables', "toc(marker='')", 'meta']


def render_html(**kwargs):
    """ Renders an html from jinja2 templates filled with content converted
        from markdown source
        Mandatory arguments:
         - input_file: markdown input file object (passed to md2html)

        Optional arguments:

        - html_template:  Template for jinja2
        - output_file:    Writtable output file descriptor object
        - css_files:      List of CSS styles to be applied to the HTML file
        - favicon_file:   Optional favicon file
        - background_img: Optional background image file
        - md_extensions:  List of extensions for markdown module (for md2html)
    """

    html_template = kwargs.pop('html_template', HTML_TEMPLATE)
    css_files = kwargs.pop('css_files', [])
    output_file_descr = kwargs.pop('output_file', None)
    favicon_file = kwargs.pop('favicon', None)
    background_img = kwargs.pop('background_img', None)
    logo_img = kwargs.pop('logo', None)

    loader = jinja2.FileSystemLoader(THIS_DIR)
    environment = jinja2.Environment(loader=loader,
                                     trim_blocks=True)
    environment.globals['include_raw'] = \
        lambda filename: jinja2.Markup(loader.get_source(environment,
                                                         filename)[0]) \
        if os.path.exists(filename) else ''

    environment.globals['gen_author_list'] = \
        lambda authors, emails: [''] if len(authors) != len(emails) else \
        [u'<a href="mailto:{}">{}</a>'.format(emails[i], author)
         for (i, author) in enumerate(authors)]

    environment.globals['gen_copyright_list'] = \
        lambda copyright: [u'<a href={1}>{0}</a>'.format(*item.split(','))
                           for item in copyright]

    environment.globals['css_compress'] = \
        lambda css_list: ';'.join(css_compress(*['css/%s' % css
                                                 for css in css_list]))

    template = environment.get_template(html_template)
    content, metadata, toc = md2html(**kwargs)

    fbuffer = StringIO()
    fbuffer.write(template.render(css_lines=';'.join(css_compress(*css_files)),
                                  content=content,
                                  metadata=metadata,
                                  toc=toc,
                                  favicon=to_b64_image(favicon_file),
                                  logo=to_b64_image(logo_img),
                                  background=to_b64_image(background_img),
                                  date=date.today()).encode('utf-8'))
    fbuffer.seek(0)
    html_str = reencode_html(fbuffer)
    if output_file_descr:
        output_file_descr.write(html_str)
    else:
        print(html_str)


def reencode_html(input_html):
    """
    Converts all images from an html file to base64
    """
    fbuffer = StringIO()
    my_regex = re.compile('.*(<img.+src=\")(.+?)"', re.IGNORECASE)
    for line in input_html:
        try:
            item = re.finditer(my_regex, line).next().group(2)
            fbuffer.write(line.replace(item, to_b64_image(item)))
        except StopIteration:
            fbuffer.write(line)
    fbuffer.seek(0)
    return fbuffer.read()


def css_compress(*css_files):
    """ Reads file by file and returns the compressed version of the CSS """
    for item in css_files:
        with open(item, 'r') as css_file:
            yield compress(css_file.read())


def to_b64_image(image_filename):
    """ Returns a tuple with (b64content, imgtype) where:
        - b64content is a base64 representation of the input file
        - imgtype is the image type as detected by imghdr
    """
    try:
        img_info = parse(image_filename, rule='IRI')
        extension = img_info['path'].split('.')[-1]
        content = urlopen(image_filename)
    except ValueError:  # image_filename is not a valid IRI, assume local file
        extension = imghdr.what(image_filename)
        if extension is None:
            return None
        content = open(image_filename, 'rb')
    except (IOError, AttributeError, TypeError):
        return None
    txt = 'data:image/{};base64,\n{}'.format(extension,
                                            content.read().encode('base64'))
    content.close()
    return txt


def md2html(**kwargs):
    """ Converts markdown syntax to html
        kwargs:
         - input_file: markdown input file object
         - md_extensions [optional]: list of extensions for markdown module

        Returns:
        - html:    HTML encoded string
        - md.Meta: Metadata as found in md header (if any)
        - md.toc:  Table of Contents, if TOC in md_extensions
    """

    md_fileobject = kwargs.get('input_file', None)
    assert md_fileobject is not None

    md_extensions = kwargs.get('md_extensions', MD_EXTENSIONS)
    md_content = markdown.Markdown(extensions=['markdown.extensions.%s' % k
                                               for k in md_extensions])
    html = md_content.convert(md_fileobject.read().decode('utf-8'))
    if 'toc' in md_extensions:
        if 'meta' in md_extensions:
            return (html, md_content.Meta, md_content.toc)
        else:
            return (html, None, md_content.toc)
    else:
        if 'meta' in md_extensions:
            return (html, md_content.Meta, None)
        else:
            return (html, None, None)

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Markdown to HTML converter',
                                     formatter_class=argparse.
                                     RawTextHelpFormatter)

    PARSER.add_argument('-C', '--css', metavar='CSS_FILE',
                        dest='css_files', nargs='+', default=[],
                        type=str, help='CSS files')

    PARSER.add_argument('-T', '--template',
                        dest='html_template', default=HTML_TEMPLATE,
                        type=str, help='HTML template for Jinja2')

    PARSER.add_argument('-F', '--favicon',
                        dest='favicon',
                        type=str, help='PNG/BMP/JPG favicon')

    PARSER.add_argument('-B', '--background',
                        dest='background_img',
                        type=str, help='PNG/BMP/JPG background image')

    PARSER.add_argument('-L', '--logo',
                        dest='logo',
                        type=str, help='Logo image (PNG/BMP/JPG)')

    PARSER.add_argument('-M', '--extensions', metavar='MARKDOWN_EXTENSIONS',
                        dest='md_extensions', nargs='+', default=MD_EXTENSIONS,
                        type=str, help='Extensions from markdown module')

    PARSER.add_argument('input_file', default=sys.stdin,
                        type=argparse.FileType('r'),
                        help='Markdown input file')

    PARSER.add_argument('-O', '--output_file', default=sys.stdout,
                        type=argparse.FileType('w'),
                        help='HTML output file, defaults to stdout')

    ARGS = PARSER.parse_args()

    render_html(**vars(ARGS))
#    import codecs
#    fichero = codecs.open('prueba.md', mode='r', encoding='utf-8')
#    render_html(input_file=fichero)
