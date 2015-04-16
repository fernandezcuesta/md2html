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
import time
from cStringIO import StringIO
from rfc3987 import parse
from urllib2 import urlopen, HTTPError, URLError
from csscompressor import compress


HTML_TEMPLATE = 'template.html'
MD_EXTENSIONS = ['codehilite', 'tables', "toc(marker='')", 'meta']


def to_b64(image_filename):
    """ Returns a tuple with (b64content, imgtype) where:
        - b64content is a base64 representation of the input file
        - imgtype is the image type as detected by imghdr
    """
    try:
        img_info = parse(image_filename, rule='IRI')
        extension = img_info['path'].split('.')[-1]
        content = urlopen(image_filename)
    except ValueError:  # not a valid IRI, assume local file
        try:
            extension = imghdr.what(image_filename)
            if extension is None:
                return None
            content = open(image_filename, 'rb')
        except (IOError, AttributeError, TypeError):
            return None
    except (HTTPError, URLError, TypeError):
        return None
    txt = 'data:image/{};base64,\n{}'.format(extension,
                                             content.read().encode('base64'))
    content.close()
    return txt


def reencode_html(input_html):
    """
    Embeds all images from an html file to base64
    """
    fbuffer = StringIO()
    my_regex = re.compile('.*(<img.+src=\")(.+?)"', re.IGNORECASE)
    for line in input_html:
        try:
            item = re.finditer(my_regex, line).next().group(2)
            fbuffer.write(line.replace(item, to_b64(item)))
        except StopIteration:
            fbuffer.write(line)
    fbuffer.seek(0)
    content = fbuffer.read()
    fbuffer.close()
    return content


class MD2Html(object):

    """
    Main class object
    """

    def __init__(self):
        self.working_dir = os.getcwd()
#                     os.path.dirname(os.path.abspath(__file__))
        self.html_template = HTML_TEMPLATE
        self.md_extensions = MD_EXTENSIONS

    def main(self, **kwargs):
        """ Renders an html from jinja2 templates filled with content converted
            from markdown source
            Mandatory arguments:
            - md_fileobject: markdown input file object (passed to get_html)

            Optional arguments:

            - html_template:  Template for jinja2
            - output_file:    Writtable output file descriptor object
            - css_files:      List of CSS files to be applied to the HTML
            - favicon_file:   Optional favicon file
            - background_img: Optional background image file
            - md_extensions:  List of extensions for markdown module
            - working_dir:    Directory where /layout and /css are found
        """

        self.html_template = kwargs.get('html_template', self.html_template)
        self.working_dir = kwargs.get('working_dir', self.working_dir)
        self.md_extensions = kwargs.get('md_extensions', self.md_extensions)

        css_files = kwargs.get('css_files', [])
        output_file_descr = kwargs.get('output_file', None)
        favicon_file = kwargs.get('favicon', None)
        background_img = kwargs.get('background_img', None)
        logo_img = kwargs.get('logo', None)

        loader = jinja2.FileSystemLoader('{}/layout'.format(self.working_dir))
        environment = jinja2.Environment(loader=loader, trim_blocks=True)
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

        environment.globals['css_compress'] = self.css_compress

        environment.globals['to_base64'] = \
            lambda image: to_b64(image[0])

        template = environment.get_template(self.html_template)
        content, metadata, toc = self.get_html(kwargs.get('md_fileobject'))

        if 'logo' in metadata:  # input argument overrides MD's metadata
            logo_img = logo_img or metadata['logo'][0]

        if 'favicon' in metadata:  # input argument overrides MD's metadata
            favicon_file = favicon_file or metadata['favicon'][0]

        if 'background' in metadata:
            background_img = background_img or metadata['background'][0]

        markdown_date = ', '.join(metadata['date']) if 'date' in metadata \
            else time.strptime('%d-%B-%Y')

        fbuffer = StringIO()
        fbuffer.write(template.render(css_lines=self.css_compress(css_files),
                                      content=content,
                                      metadata=metadata,
                                      toc=toc,
                                      favicon=to_b64(favicon_file),
                                      logo=to_b64(logo_img),
                                      background=to_b64(background_img),
                                      date=markdown_date).encode('utf-8'))
        fbuffer.seek(0)
        if output_file_descr:
            output_file_descr.write(reencode_html(fbuffer))
        else:
            print(reencode_html(fbuffer))
        fbuffer.close()
        return

    def css_compress(self, css_files):
        """ Reads file by file and returns the compressed version of the CSS
        css_files: list of files, located in /css subfolder
        """
        def css_wrapper(css_files):
            """ Wrapper for css_compress handling with non-existing files """
            for item in css_files:
                try:
                    with open('{}/{}'.format(self.working_dir, item),
                              'r') as css_file:
                        yield compress(css_file.read())
                except IOError:
                    yield ''

        return ''.join(css_wrapper(['css/%s' % css for css in css_files]))

    def get_html(self, md_fileobject):
        """ Converts markdown syntax to html
             - md_fileobject: markdown input file object

            Returns:
            - html:    HTML encoded string
            - md.Meta: Metadata as found in md header (if any)
            - md.toc:  Table of Contents, if TOC in md_extensions
        """
        md_content = markdown.Markdown(extensions=['markdown.extensions.%s' % k
                                                   for k in self.md_extensions]
                                       )
        html = md_content.convert(md_fileobject.read().decode('utf-8'))
        if any(['toc' in k for k in self.md_extensions]):
            if 'meta' in self.md_extensions:
                return (html, md_content.Meta, md_content.toc)
            else:
                return (html, None, md_content.toc)
        else:
            if 'meta' in self.md_extensions:
                return (html, md_content.Meta, None)
            else:
                return (html, None, None)

if __name__ == "__main__":

    MD_TO_HTML = MD2Html()
    PARSER = argparse.ArgumentParser(description='Markdown to HTML converter',
                                     formatter_class=argparse.
                                     RawTextHelpFormatter)

    PARSER.add_argument('-C', '--css', metavar='CSS_FILE',
                        dest='css_files', nargs='+', default=[],
                        type=str, help='CSS files')

    PARSER.add_argument('-T', '--template',
                        dest='html_template', default=MD_TO_HTML.html_template,
                        type=str, help='HTML template for Jinja2, defaults to '
                                       '{}'.format(MD_TO_HTML.html_template))

    PARSER.add_argument('-F', '--favicon',
                        dest='favicon',
                        type=str, help='PNG/BMP/JPG favicon')

    PARSER.add_argument('-B', '--background',
                        dest='background_img',
                        type=str, help='PNG/BMP/JPG background image')

    PARSER.add_argument('-L', '--logo',
                        dest='logo',
                        type=str, help='Logo image (PNG/BMP/JPG)')

    PARSER.add_argument('-M', '--extensions', metavar='MARKDOWN_EXTENSION',
                        dest='md_extensions', nargs='+', type=str,
                        default=MD_TO_HTML.md_extensions,
                        help='Extensions from markdown module, defaults to '
                             '{}'.format(MD_TO_HTML.md_extensions))

    PARSER.add_argument('md_fileobject', default=sys.stdin,
                        type=argparse.FileType('r'), metavar='input_file',
                        help='Markdown input file')

    PARSER.add_argument('-O', '--output_file', default=sys.stdout,
                        type=argparse.FileType('w'),
                        help='HTML output file, defaults to stdout')

    ARGS = PARSER.parse_args()
    MD_TO_HTML.main(**vars(ARGS))
