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
import logging
import codecs

from cStringIO import StringIO
from rfc3987 import parse
from urllib2 import urlopen, HTTPError, URLError
from csscompressor import compress
from datetime import date
from dateutil.parser import parse as date_parse

HTML_TEMPLATE = 'template.html'
MD_EXTENSIONS = ["codehilite", "tables", "toc(marker='')", "meta"]
DEFAULT_LOGLEVEL = 'INFO'


def init_logger(loglevel=None, name=__name__):
    """ Initialize logger, sets the appropriate level and attaches a console
        handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(loglevel or DEFAULT_LOGLEVEL)

    # If no console handlers yet, add a new one
    if not any(isinstance(x, logging.StreamHandler) for x in logger.handlers):
        console_handler = logging.StreamHandler()
        if logging.getLevelName(logger.level) == 'DEBUG':
            _fmt = '%(asctime)s| %(levelname)-8s| %(threadName)10s/' \
                   '%(lineno)03d@%(module)-10s| %(message)s'
            console_handler.setFormatter(logging.Formatter(_fmt))
        else:
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s| %(levelname)-8s| %(message)s'))
        logger.addHandler(console_handler)

    logger.info('Initialized logger with level: %s',
                logging.getLevelName(logger.level))
    return logger


class MD2Html(object):

    """
    Main class object
    """

    def __init__(self):
        self.working_dir = os.getcwd()
        self.html_template = HTML_TEMPLATE
        self.md_extensions = MD_EXTENSIONS
        self.logger = init_logger()

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
            - loglevel:       Debug level passed to logging
        """
        # Remove all "None" input values
        list(map(kwargs.pop, [item for item in kwargs if not kwargs[item]]))

        self.html_template = kwargs.get('html_template', self.html_template)
        self.working_dir = kwargs.get('working_dir', self.working_dir)
        self.md_extensions = kwargs.get('md_extensions', self.md_extensions)
        if 'loglevel' in kwargs:
            self.logger.setLevel(kwargs.get('loglevel'))
        css_files = kwargs.get('css_files', [])
        output_file_descr = kwargs.get('output_file', None)
        favicon_file = kwargs.get('favicon', None)
        background_img = kwargs.get('background_img', None)
        logo_img = kwargs.get('logo', None)

        self.logger.debug('Loading template %s/layout/%s',
                          self.working_dir,
                          self.html_template)
        loader = jinja2.FileSystemLoader('{}/layout'.format(self.working_dir))
        environment = jinja2.Environment(loader=loader, trim_blocks=True)

#       FUNCTIONS PASSED TO JINJA2
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
            lambda image: self.to_b64(image[0])

        template = environment.get_template(self.html_template)
        content, metadata, toc = self.get_html(kwargs.get('md_contents'))

        if 'logo' in metadata:  # input argument overrides MD's metadata
            logo_img = logo_img or metadata['logo'][0]

        if 'favicon' in metadata:  # input argument overrides MD's metadata
            favicon_file = favicon_file or metadata['favicon'][0]

        if 'background' in metadata:
            background_img = background_img or metadata['background'][0]

        try:
            markdown_date = date_parse(metadata['date'][0]) \
                            if 'date' in metadata else date.today()
        except ValueError:  # date in markdown not recognized by parser
            print """
            Date in markdown not recognized by parser (wrong locale?)
            Aborting..."""
            return

        fbuffer = StringIO()
        fbuffer.write(template.render(css_lines=self.css_compress(css_files),
                                      content=content,
                                      metadata=metadata,
                                      toc=toc,
                                      favicon=self.to_b64(favicon_file),
                                      logo=self.to_b64(logo_img),
                                      background=self.to_b64(background_img),
                                      date=markdown_date).encode('utf-8'))
        fbuffer.seek(0)
        if output_file_descr:
            output_file_descr.write(self.reencode_html(fbuffer))
        else:
            print(self.reencode_html(fbuffer))
        fbuffer.close()
        return

    def to_b64(self, image_filename):
        """ Returns a tuple with (b64content, imgtype) where:
            - b64content is a base64 representation of the input file
            - imgtype is the image type as detected by imghdr
        """
        self.logger.debug('Converting image %s to base64', image_filename)
        try:
            img_info = parse(image_filename, rule='IRI')
            extension = img_info['path'].split('.')[-1]
            content = urlopen(image_filename)
        except ValueError:  # not a valid IRI, assume local file
            self.logger.debug("Image doesn't have a valid URL, assuming local")
            try:
                extension = imghdr.what(image_filename)
                if extension is None:
                    self.logger.debug('Image extension not detedted, skipping')
                    return None
                content = open(image_filename, 'rb')
            except (IOError, AttributeError, TypeError):
                return None
        except (HTTPError, URLError, TypeError):
            return None
        txt = 'data:image/{};base64,\n{}'.format(extension,
                                                 content.read().encode('base64'
                                                                       )
                                                 )
        content.close()
        return txt

    def reencode_html(self, input_html):
        """
        Embeds all images from an html file to base64
        """
        fbuffer = StringIO()
        my_regex = re.compile('.*(<img.+src=\")(.+?)"', re.IGNORECASE)
        for line in input_html:
            try:
                item = re.finditer(my_regex, line).next().group(2)
                self.logger.debug('Embedding image: %s',
                                  item)
                fbuffer.write(line.replace(item, self.to_b64(item)))
            except StopIteration:
                fbuffer.write(line)
        fbuffer.seek(0)
        content = fbuffer.read()
        fbuffer.close()
        return content

    def css_compress(self, css_files):
        """ Reads file by file and returns the compressed version of the CSS
        css_files: list of files, located in /css subfolder
        """
        def css_wrapper(css_files, ):
            """ Wrapper for css_compress handling with non-existing files """
            for item in css_files:
                try:
                    self.logger.debug('Loading CSS %s/css/%s',
                                      self.working_dir,
                                      item)
                    with open('{}/css/{}'.format(self.working_dir, item),
                              'r') as css_file:
                        yield compress(css_file.read())
                except IOError:
                    yield ''

        return ''.join([css for css in css_wrapper(css_files)])

    def get_html(self, md_contents):
        """ Converts markdown syntax to html
             - md_contents: markdown input file content

            Returns:
            - html:    HTML encoded string
            - md.Meta: Metadata as found in md header (if any)
            - md.toc:  Table of Contents, if TOC in md_extensions
        """
        extensions = ['markdown.extensions.%s' % k for k in self.md_extensions]
        self.logger.debug('Generating markdown with extensions: %s',
                          ', '.join(extensions))
        md_content = markdown.Markdown(extensions=extensions)
        html = md_content.convert(md_contents)  #.decode('utf-8'))
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

def mdfile(input_file):
    """ Open the input file detecting the encoding (UTF-8 with BOM) """
    try:
        bytes = min(32, os.path.getsize(input_file))
        with open(input_file, 'rb') as raw:
            header = raw.read(bytes)
    
            if header.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'
            elif header.startswith(codecs.BOM_UTF16_LE) or \
                 header.startswith(codecs.BOM_UTF16_BE):
                encoding = 'utf-16'
            elif header.startswith(codecs.BOM_UTF32_LE) or \
                 header.startswith(codecs.BOM_UTF32_BE):
                encoding = 'utf-32'
            else:
                encoding = 'utf-8'
            
            raw.seek(0)
            data = raw.read().decode(encoding)
        return data
    except OSError:
        raise argparse.ArgumentTypeError("No such file: %s" % input_file)

if __name__ == "__main__":

    MD_TO_HTML = MD2Html()
    PARSER = argparse.ArgumentParser(description='Markdown to HTML converter',
                                     formatter_class=argparse.
                                     RawTextHelpFormatter)

    PARSER.add_argument('-C', '--css', metavar='CSS_FILE',
                        dest='css_files', nargs='+', default=[],
                        type=str, help='CSS files')

    PARSER.add_argument('-W', '--working-dir', metavar='BASE_FOLDER',
                        dest='working_dir', default=os.getcwd(),
                        type=str, help='Working base directory where '
                                       '/css and /layout folders are found')

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

    PARSER.add_argument('md_contents',
                        type=mdfile, metavar='input_file',
                        help='Markdown input file')

    PARSER.add_argument('-O', '--output_file', default=sys.stdout,
                        type=argparse.FileType('w'),
                        help='HTML output file, defaults to stdout')

    PARSER.add_argument('--loglevel', const="WARNING",
                        choices=['DEBUG',
                                 'INFO',
                                 'WARNING',
                                 'ERROR',
                                 'CRITICAL'],
                        help='Debug level (default: %s)' % DEFAULT_LOGLEVEL,
                        nargs='?')

    ARGS = PARSER.parse_args()
    MD_TO_HTML.main(**vars(ARGS))

