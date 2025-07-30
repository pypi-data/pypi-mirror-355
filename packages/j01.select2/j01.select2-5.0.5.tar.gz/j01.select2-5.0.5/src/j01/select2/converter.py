##############################################################################
#
# Copyright (c) 2007 Projekt01 GmbH.
# All Rights Reserved.
#
##############################################################################
"""
from __future__ import unicode_literals
$Id: converter.py 5204 2025-04-05 19:29:08Z felipe.souza $
"""
from __future__ import absolute_import
__docformat__ = 'restructuredtext'

import zope.component
import zope.schema
import zope.schema.interfaces

from z3c.form import widget

from z3c.form import widget
from z3c.form import converter

from j01.select2 import interfaces


class SingleTagConverter(converter.BaseDataConverter):
    """Converter between ITextLine and ISingleTagSelect2Widget"""

    zope.component.adapts(zope.schema.interfaces.IField,
        interfaces.ISingleTagSelect2Widget)

    def toWidgetValue(self, value):
        """Convert from Python bool to HTML representation."""
        # if the value is the missing value, then an empty list is produced.
        if value is self.field.missing_value:
            return []
        else:
            return [value]

    def toFieldValue(self, value):
        """See interfaces.IDataConverter"""
        if not len(value) or value[0] == self.widget.noValueToken:
            return self.field.missing_value
        return value[0]


class TagListConverter(converter.BaseDataConverter):
    """Converter between IList of ITextLine and ITagListSelect2Widget"""

    zope.component.adapts(zope.schema.interfaces.IList,
        interfaces.ITagListSelect2Widget)

    def toWidgetValue(self, value):
        """Convert from Python to HTML representation."""
        if not len(value) or value[0] == self.widget.noValueToken:
            return self.field.missing_value or []
        else:
            return value

    def toFieldValue(self, value):
        """See interfaces.IDataConverter"""
        if not len(value):
            return self.field.missing_value or []
        else:
            return value


class LiveListConverter(converter.CollectionSequenceDataConverter):
    """Data converter for ILiveListSelect2Widget.

    This converter reqires a LivList widget providing LiveListTerms where we
    can lookup existing values based on term tokens.
    """

    zope.component.adapts(
        zope.schema.interfaces.IList, interfaces.ILiveListSelect2Widget)

    def toFieldValue(self, value):
        """See interfaces.IDataConverter"""
        widget = self.widget
        if not len(value):
            return self.field.missing_value or []
        if widget.terms is None:
            widget.updateTerms()
        return [widget.terms.getValue(token) for token in value]