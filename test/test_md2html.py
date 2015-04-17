#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
md2html - test functions
"""

import unittest
import md2html
import filecmp
from cStringIO import StringIO


class TestMd2html(unittest.TestCase):
    """ Set of test functions for md2html module """

    def __init__(self, *args, **kwargs):
        super(TestMd2html, self).__init__(*args, **kwargs)
        self.test = md2html.MD2Html()
        self.test.logger.setLevel('DEBUG')

    def test_to_b64(self):
        """ Test function for MD2Html.to_b64() """
        local_image = "../md2html/layout/images/Acme-logo.png"
        remote_image = "http://upload.wikimedia.org/wikipedia/"\
                       "commons/7/7e/Acme-logo.png"
        self.assertIsNotNone(self.test.to_b64(local_image))
        self.assertIsNotNone(self.test.to_b64(remote_image))
        self.assertEqual(self.test.to_b64(local_image),
                         self.test.to_b64(remote_image))
        self.assertIsNone(self.test.to_b64('nonexisting_file.png'))
        self.assertIsNone(self.test.to_b64('http://localhost/nofile.jpg'))
        self.assertIsNone(self.test.to_b64('http://wrong.url/img.png'))

    def test_reencodehtml(self):
        """ Test function for MD2Html.reencode_html() """
        html = ['<html><body><h1>TITLE</h1><a>Hello World!</a>',
                '</body></html>']
        self.assertEqual(self.test.reencode_html(html),
                         ''.join(html))
        html = ['<html><body><h1>TITLE</h1><a>Hello World!</a>',
                '<img src="../md2html/layout/images/Acme-logo.png" />',
                '</body></html>']
        self.assertIn('data:image/png;base64,', self.test.reencode_html(html))

    def test_csscompress(self):
        """ Test function for MD2Html.css_compress() """
        self.assertListEqual([k for k in self.test.css_compress([])], [])
        css_files = ['../md2html/css/lanyon.css',
                     '../md2html/css/codehilite.css']
        css_comp1 = self.test.css_compress(css_files)
        self.assertIsNotNone(''.join([css for css in css_comp1]))

        css_comp1 = self.test.css_compress(css_files)
        css_comp2 = self.test.css_compress(css_files + ['nonexisting.css'])
        self.assertEqual(''.join([css for css in css_comp1]),
                         ''.join([css for css in css_comp2]))

    def test_gethtml(self):
        """ Test function for MD2Html.get_html() """
        md_string = '#Title\n##This is my markdown file!\n![Alt](!'\
                    'https://duckduckgo.com/assets/badges/logo_square.64.png'\
                    ')\n`End of file`'

        fbuffer = StringIO()
        fbuffer.write(md_string)

        fbuffer.seek(0)
        self.test.md_extensions = []
        html = self.test.get_html(fbuffer)
        self.assertMultiLineEqual(html[0],
                                  '<h1>Title</h1>\n'
                                  '<h2>This is my markdown file!</h2>\n'
                                  '<p><img alt="Alt" src="!https://duckduckgo'
                                  '.com/assets/badges/logo_square.64.png" />\n'
                                  '<code>End of file</code></p>')
        self.assertIsNone(html[1])
        self.assertIsNone(html[2])

        fbuffer.seek(0)
        self.test.md_extensions = md2html.MD_EXTENSIONS
        html = self.test.get_html(fbuffer)
        self.assertDictEqual(html[1], {})  # empty metadata
        fbuffer.close()

        fbuffer = StringIO()
        fbuffer.write('metadata: metadata example\n%s' % md_string)
        fbuffer.seek(0)
        html = self.test.get_html(fbuffer)
        map(self.assertIsNotNone, html)
        self.assertDictEqual(html[1],
                             {u'metadata': [u'metadata example']})
        fbuffer.close()

    def test_main(self):
        """ End to end test of overall module by running MD2Html.main()
        """
        tmp_file = StringIO()
        with open('test.md', 'r') as md_fileobject:
            self.test.main(md_fileobject=md_fileobject,
                           output_file=tmp_file,
                           working_dir='../md2html')
        with open('test.html', 'r') as htmlfile:
            that = htmlfile.read()
        tmp_file.seek(0)
        this = tmp_file.read()
        self.assertMultiLineEqual(this, that)


if __name__ == '__main__':
    unittest.main()
