import unittest

import pathext


class PathextTests(unittest.TestCase):

    def assertEquAll(self, *args):
        last = args[-1]

        for arg in args[:-1]:
            self.assertEqual(arg, last)

    def assertAllTrue(self, *args):
        for arg in args:
            self.assertTrue(arg)

    def assertAllFalse(self, *args):
        for arg in args:
            self.assertFalse(arg)

    def test_split_path(self):
        self.assertEquAll(
            pathext.split('dev/python-dev/syncall/'),
            pathext.split('dev/python-dev///syncall'),
            ('dev', 'python-dev', 'syncall')
        )
        self.assertEquAll(
            pathext.split('/dev/python-dev/syncall'),
            pathext.split('/dev/python-dev/syncall/'),
            pathext.split('/dev//python-dev/syncall/'),
            ('/', 'dev', 'python-dev', 'syncall')
        )

    def test_empty_split(self):
        self.assertEqual(
            pathext.split(''),
            ('',)
        )

    def test_common_prefix(self):
        self.assertEqual(
            pathext.split(pathext.common_prefix(
                'dev/python/tests/',
                'dev/python/test'
            )),
            ('dev', 'python')
        )

    def test_empty_common_prefix(self):
        self.assertEqual(
            pathext.split(pathext.common_prefix(
                'dev/python/tests/',
                '/dev/python/test'
            )),
            ('',)
        )

    def test_longest_prefix(self):
        self.assertEqual(
            pathext.split(pathext.longest_prefix(
                '/dev/python-dev/some/long/directory/file.py',
                [
                    '/dev/',
                    'dev/python-dev/some/long/directory/',
                    '/dev/python-dev/some',
                    '/dev/python-dev/some/lon'
                ]
            )),
            ('/', 'dev', 'python-dev', 'some')
        )

    def test_empty_longest_prefix(self):
        self.assertEqual(
            pathext.longest_prefix(
                'dev/python-dev/some/long/dir',
                [
                    '/dev/python-dev/some',
                    '/developer/pypy/stuff',
                    'etc/'
                ]
            ),
            ''
        )

    def test_is_direct_child(self):
        self.assertAllTrue(
            pathext.is_direct_child('/dev', '/dev/python'),
            pathext.is_direct_child('dev', 'dev/python'),
            pathext.is_direct_child('dev/py', 'dev//py//python'),
        )

        self.assertAllFalse(
            pathext.is_direct_child('/dev/python', '/dev'),
            pathext.is_direct_child('/devel', '/dev/python'),
            pathext.is_direct_child('/dev/py', '/dev/python'),
        )
