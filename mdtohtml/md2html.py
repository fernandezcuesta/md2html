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


class MyLoader(jinja2.BaseLoader):

    def __init__(self, sourcepath, logger):
        self.path = os.path.dirname(sourcepath)
        self.logger = logger

#TODO: write a test function for including raw HTML
    def get_source(self, environment, template):
        path = os.path.abspath(os.path.relpath(template, self.path))
        self.logger.debug('Rendering %s', path)

        if not os.path.exists(path):
            raise jinja2.TemplateNotFound(template)
        mtime = os.path.getmtime(path)
        with file(path) as f:
            source = f.read().decode('utf-8')
        return source, path, lambda: mtime == os.path.getmtime(path)


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
        self.working_dir = os.path.dirname(os.path.abspath(__file__))
        self.html_template = HTML_TEMPLATE
        self.md_extensions = MD_EXTENSIONS
        self.logger = init_logger()

    def main(self, md_file, **kwargs):
        """ Renders an html from jinja2 templates filled with content converted
            from markdown source
            Mandatory arguments:
            - md_contents: markdown input file content (passed to get_html)

            Optional arguments:

            - html_template:  Template for jinja2
            - output_file:    Writtable output file descriptor object
            - md_extensions:  List of extensions for markdown module
            - working_dir:    Directory where /layout and /css are found
            - loglevel:       Debug level passed to logging
        """
        # Remove all "None" input values
        list(map(kwargs.pop, [item for item in kwargs if not kwargs[item]]))
        if 'loglevel' in kwargs:
            self.logger.setLevel(kwargs.get('loglevel'))
        self.html_template = kwargs.get('html_template', self.html_template)
        self.working_dir = kwargs.get('working_dir', self.working_dir)

        if not os.path.isfile('%s/layout/%s' % (self.working_dir,
                                                self.html_template)):
            self.logger.error('Base template "%s" not found in %s/layout.',
                              self.html_template,
                              self.working_dir)
            return

        self.md_extensions = kwargs.get('md_extensions', self.md_extensions)
        output_file_descr = kwargs.get('output_file', None)

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

        environment.globals['hrefs_from_keypair'] = \
            lambda keypair: [u'<a href={1}>{0}</a>'.format(*item.split(','))
                             for item in keypair]

        environment.globals['hrefs_from_lists'] = \
            lambda names, links: [''] if len(names) != len(links) else \
            [u'<a href={}>{}</a>'.format(links[i], name) for (i, name)
             in enumerate(names)]

        environment.globals['css_compress'] = self.css_compress

        environment.globals['to_base64'] = \
            lambda image: self.to_b64(image[0])
#       END OF FUNCTIONS PASSED TO JINJA2

        template = environment.get_template(self.html_template)
        content, metadata, toc = self.get_html(md_file)

        try:
            markdown_date = date_parse(metadata['date'][0]) \
                            if 'date' in metadata else date.today()
        except ValueError:  # date in markdown not recognized by parser
            print "Date in markdown not recognized by parser (wrong locale?)"
            markdown_date = None

        fbuffer = StringIO()
        rendered = template.render(content=content,
                                   metadata=metadata,
                                   toc=toc,
                                   date=markdown_date,
                                   **kwargs)

        # MD may contain a {% include 'that.html' %}, 2nd rendering pass needed
        if kwargs.get('2pass', None):
            self.logger.info('Second pass rendering MD Jinja2 references')
            loader = MyLoader(os.path.abspath(md_file), self.logger)
            environment = jinja2.Environment(loader=loader, trim_blocks=True)
            template = environment.from_string(rendered)
            fbuffer.write(template.render().encode('utf-8'))
        else:
            fbuffer.write(rendered.encode('utf-8'))

        fbuffer.seek(0)
        self.logger.debug('Rendering OK')

        if output_file_descr:
            output_file_descr.write(self.reencode_html(fbuffer))
        else:
            print(self.reencode_html(fbuffer))
        fbuffer.close()
        return

    def to_b64(self, image_filename, *args):
        """ Returns a tuple with (b64content, imgtype) where:
            - b64content is a base64 representation of the input file
            - imgtype is the image type as detected by imghdr
        """
        self.logger.debug('Converting image %s to base64', image_filename)
        self.logger.debug('Current directory %s', os.path.abspath(os.curdir))
        try:
            img_info = parse(image_filename, rule='IRI')
            extension = img_info['path'].split('.')[-1]
            content = urlopen(image_filename)
        except ValueError:  # not a valid IRI, assume local file
            self.logger.debug("Image '%s' doesn't have a valid URL, "
                              "assuming local", image_filename)
            try:
                extension = imghdr.what(image_filename)
                if extension is None:
                    self.logger.debug('Image extension not detected, skipping')
                    return ''
                content = open(image_filename, 'rb')
            except (IOError, AttributeError, TypeError):
                return ''
        except (HTTPError, URLError, TypeError):
            return ''
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
                        yield '/* CSS from metadata: {} */ {}'.format(
                                                     item,
                                                     compress(css_file.read()))
                except IOError:
                    yield ''

        return ''.join([css for css in css_wrapper(css_files)])

    def get_html(self, md_file):
        """ Converts markdown syntax to html
             - md_file: markdown input file name

            Returns:
            - html:    HTML encoded string
            - md.Meta: Metadata as found in md header (if any)
            - md.toc:  Table of Contents, if TOC in md_extensions
        """
        extensions = ['markdown.extensions.%s' % k for k in self.md_extensions]
        self.logger.debug('Generating markdown with extensions: %s',
                          ', '.join(extensions))
        md_converter = markdown.Markdown(extensions=extensions)
        md_content = self.read_mdfile(md_file)
        html = md_converter.convert(md_content)

        if any(['toc' in k for k in self.md_extensions]):
            if 'meta' in self.md_extensions:
                return (html, md_converter.Meta, md_converter.toc)
            else:
                return (html, None, md_converter.toc)
        else:
            if 'meta' in self.md_extensions:
                return (html, md_converter.Meta, None)
            else:
                return (html, None, None)

    def read_mdfile(self, input_file):
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
        except OSError as exception:
            self.logger.error('No such file: %s', input_file)
            raise exception
