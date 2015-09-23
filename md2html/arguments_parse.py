#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:18:42 2015

@author: fernandezjm
"""

import os, sys
import argparse
import md2html


def arguments_parse():
    """ Argument parser for main method
    """
    MD_TO_HTML = md2html.MD2Html()
    parser = argparse.ArgumentParser(formatter_class=argparse.
                                     RawTextHelpFormatter,
                                     description='Markdown to HTML converter')

    parser.add_argument('-C', '--css', metavar='CSS_FILE',
                        dest='css_files', nargs='+', default=[],
                        type=str, help='CSS files')

    parser.add_argument('-W', '--working-dir', metavar='BASE_FOLDER',
                        dest='working_dir', default=MD_TO_HTML.working_dir,
                        type=str, help='Working base directory where '
                                       '/css and /layout folders are found')

    parser.add_argument('-T', '--template',
                        dest='html_template', default=MD_TO_HTML.html_template,
                        type=str, help='HTML template for Jinja2')

    parser.add_argument('-M', '--extensions', metavar='MARKDOWN_EXTENSION',
                        dest='md_extensions', nargs='+', type=str,
                        default=MD_TO_HTML.md_extensions,
                        help='Extensions from markdown module, defaults to '
                             '{}'.format(MD_TO_HTML.md_extensions))

    parser.add_argument('md_file',
                        type=str, metavar='input_file',
                        help='Markdown input file')

    parser.add_argument('-O', '--output_file', default=sys.stdout,
                        type=argparse.FileType('w'),
                        help='HTML output file, defaults to stdout')

    parser.add_argument('-2', action='store_true', dest='2pass',
                        help='Make a 2pass render, in case markdown file '
                             'contains Jinja2 syntax (i.e. {%% includes %%})')

    parser.add_argument('--loglevel', const="WARNING",
                        choices=['DEBUG',
                                 'INFO',
                                 'WARNING',
                                 'ERROR',
                                 'CRITICAL'],
                        help='Debug level (default: {})'.format(
                            md2html.DEFAULT_LOGLEVEL),
                        nargs='?')

    userargs = vars(parser.parse_args())

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        MD_TO_HTML.main(**userargs)


if __name__ == "__main__":
    arguments_parse()
