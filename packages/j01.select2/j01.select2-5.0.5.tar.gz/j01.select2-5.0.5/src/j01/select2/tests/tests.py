###############################################################################
#
# Copyright (c) 2014 Projekt01 GmbH.
# All Rights Reserved.
#
###############################################################################
"""Tests
from __future__ import unicode_literals
$Id: tests.py 5204 2025-04-05 19:29:08Z felipe.souza $
"""
from __future__ import absolute_import
__docformat__ = "reStructuredText"

import unittest
import doctest


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('checker.txt'),
        ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')