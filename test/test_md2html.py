#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
*pysmscmon* - SMSC monitoring **test functions**
"""

import unittest
import md2html
import filecmp
from cStringIO import StringIO


class TestMd2html(unittest.TestCase):
    """ Set of test functions for md2html module """

    def test_csscompress(self):
        """ Test function for css_compress """
        self.assertListEqual([k for k in md2html.css_compress([])], [])
        css_files = ['../md2html/css/lanyon.css',
                     '../md2html/css/codehilite.css']
        css_comp1 = md2html.css_compress(css_files)
        self.assertIsNotNone(''.join([css for css in css_comp1]))

        css_comp1 = md2html.css_compress(css_files)
        css_comp2 = md2html.css_compress(css_files + ['nonexisting.css'])
        self.assertEqual(''.join([css for css in css_comp1]),
                         ''.join([css for css in css_comp2]))

    def test_to_b64image(self):
        """ Test function for to_b64_image """
        local_image = "../md2html/layout/images/Acme-logo.png"
        remote_image = "http://upload.wikimedia.org/wikipedia/"\
                       "commons/7/7e/Acme-logo.png"
        self.assertIsNotNone(md2html.to_b64_image(local_image))
        self.assertIsNotNone(md2html.to_b64_image(remote_image))
        self.assertEqual(md2html.to_b64_image(local_image),
                         md2html.to_b64_image(remote_image))
        self.assertIsNone(md2html.to_b64_image('nonexisting_file.png'))
        self.assertIsNone(md2html.to_b64_image('http://localhost/nofile.jpg'))
        self.assertIsNone(md2html.to_b64_image('http://wrong.url/img.png'))

    def test_reencodehtml(self):
        """ Test function for reencode_html """
        html = ['<html><body><h1>TITLE</h1><a>Hello World!</a>',
                '</body></html>']
        self.assertEqual(md2html.reencode_html(html),
                         ''.join(html))
        html = ['<html><body><h1>TITLE</h1><a>Hello World!</a>',
                '<img src="../md2html/layout/images/Acme-logo.png" />',
                '</body></html>']
        self.assertIn('data:image/png;base64,', md2html.reencode_html(html))

    def test_md2html(self):
        """ Test function for md2html """
        md_string = '#Title\n##This is my markdown file!\n![Alt](!'\
                    'https://duckduckgo.com/assets/badges/logo_square.64.png'\
                    ')\n`End of file`'

        fbuffer = StringIO()
        fbuffer.write(md_string)

        fbuffer.seek(0)
        html = md2html.md2html(fbuffer, md_extensions=[])
        self.assertMultiLineEqual(html[0],
                                  '<h1>Title</h1>\n'
                                  '<h2>This is my markdown file!</h2>\n'
                                  '<p><img alt="Alt" src="!https://duckduckgo'
                                  '.com/assets/badges/logo_square.64.png" />\n'
                                  '<code>End of file</code></p>')
        self.assertIsNone(html[1])
        self.assertIsNone(html[2])

        fbuffer.seek(0)
        html = md2html.md2html(fbuffer)
        self.assertDictEqual(html[1], {})  # empty metadata
        fbuffer.close()

        fbuffer = StringIO()
        fbuffer.write('metadata: metadata example\n%s' % md_string)
        fbuffer.seek(0)
        html = md2html.md2html(fbuffer)
        map(self.assertIsNotNone, html)
        self.assertDictEqual(html[1],
                             {u'metadata': [u'metadata example']})
        fbuffer.close()

    def test_renderhtml(self):
        """ End to end test of overall module by running render_html """
        tmp_file = StringIO()
        with open('test.md', 'r') as md_fileobject:
            md2html.render_html(md_fileobject=md_fileobject,
                                output_file=tmp_file)
        with open('test.html', 'r') as htmlfile:
            that = htmlfile.read()
        tmp_file.seek(0)
        this = tmp_file.read()
        self.assertMultiLineEqual(this, that)


if __name__ == '__main__':
    unittest.main()
