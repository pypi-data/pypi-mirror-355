##############################################################################
#
# Copyright (c) 2007 Projekt01 GmbH.
# All Rights Reserved.
#
##############################################################################
"""
from __future__ import unicode_literals
$Id: jsonrpc.py 5344 2025-06-10 14:05:25Z roger.ineichen $
"""
from __future__ import absolute_import
__docformat__ = "reStructuredText"

import zope.interface
from zope.interface import implementer
import zope.component
from zope.publisher.interfaces.browser import IBrowserPage

from p01.jsonrpc.interfaces import IJSONRPCRequest
from p01.jsonrpc.publisher import MethodPublisher

from j01.select2 import interfaces


@implementer(interfaces.ISelect2Result)
class Select2Result(MethodPublisher):
    """JSON-RPC select2 result search method."""

    zope.component.adapts(IBrowserPage, IJSONRPCRequest)

    def j01Select2Result(self, fieldName, searchString, page):
        """Returns the select2 search result as JSON data.

        The returned value provides the following data structure:

        {
             more: false,
             results: [
                { id: "CA", text: "California" },
                { id: "AL", text: "Alabama" }
             ]
        }

        or for grouped data:

        {
            more: false,
            results: [
                { text: "Western", children: [
                    { id: "CA", text: "California" },
                    { id: "AZ", text: "Arizona" }
                ] },
                { text: "Eastern", children: [
                    { id: "FL", text: "Florida" }
                ] }
            ]
        }

        """

        # setup widget
        self.context.fields = self.context.fields.select(fieldName)
        self.context.updateWidgets()
        widget = self.context.widgets.get(fieldName)
        return widget.getSelect2Result(searchString, page)