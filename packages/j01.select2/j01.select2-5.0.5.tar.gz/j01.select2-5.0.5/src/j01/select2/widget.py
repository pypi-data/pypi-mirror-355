##############################################################################
#
# Copyright (c) 2007 Projekt01 GmbH.
# All Rights Reserved.
#
##############################################################################
"""
$Id: widget.py 5401 2025-06-16 15:07:06Z roger.ineichen $
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from builtins import object
import six

__docformat__ = 'restructuredtext'

import zope.interface
import zope.i18n
import zope.i18nmessageid
import zope.schema.interfaces
from zope.traversing.browser import absoluteURL

import z3c.form.widget
import z3c.form.browser.text
import z3c.form.browser.widget
from z3c.form.interfaces import NO_VALUE
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IFieldWidget

from j01.select2 import interfaces

_ = zope.i18nmessageid.MessageFactory('p01')


################################################################################
#
# Some things to note.
#
# We provide different widgets. For detailed information about the widgets
# read the doc string.
#
# Select2 provides custom input and input selection given from select widget.
# We provide widgets for any kind of input. Our select2 widget below provide
# input based on choice offering strict or with custom input. The offered
# options are comming from vocabulary/source or your custom implementation.
#
# Select2Widget / SingleSelect2Widget
# -----------------------------------
#
# The Select2Widget and SingleSelect2Widget provides values given from source
# or vocabulary based on the Choice or List of Choise. No custom input is
# allowed because the Choice wil not validate such custom input.
#
# The other widgets are use for TextLine, Bool, Int etc. or a List of them.
#
# TagListSelect2Widget / SingleTagSelect2Widget
# ---------------------------------------------
#
# The SingleTagSelect2Widget or TagListSelect2Widget provides a vocabulary or
# source defined in the widget and not in the schema field. This source is
# used for render the select options. Custom input is allowed and will validated
# by the underlaying schema field (text, bool, int etc.)
#
# LiveListSelect2Widget / LiveTagSelect2Widget
# --------------------------------------------
#
# The LiveListSelect2Widget and LiveTagSelect2Widget are used for custom input
# with or without any source/vocabulary. It's totaly up to you and what you
# implement as source. The posible values are looked up by the jsonrpc method.
#
# Hints
# -----
# At any time you will implement a custom widget, take care on what you use
# as select2 id/value. If you don't directly use the value as id, you must
# implement a converter converting the given id to a real value. This is often
# a custom implementation and not a simply vocaulary/soruce lookup.
#
# Our implementation will prvide the correct value lookup based on the
# vocabulary defined in Choice or List of Choice in the Selet2Widget or
# SingleSelect2Widget. The wiget is using the vocablary term token and convert
# them to a value. No special implementation is used, the implementation is
# using the default z3c.form converter for Choice or List of Choice.
#
# The other widgets allow custom input which is text. This can get mixed with
# vocabulary source terms. This eans you have to take care if you need to
# convert and validate your input to predefined values or if you allways use
# the raw input as value.
#
# The converter used for SingleTagSelect2Widget or TaglistSelect2Widget will
# just store the given input values as is (text).
#
# The LiveListSelect2Widget uses by default the ILiveListSource which provides
# terms for convert the given input to values.
#
################################################################################

j01_select2_template = """<script>
  $("#%s").select2({%s
  });
</script>
"""

NULL = object()


def j01Select2JavaScript(widgetExpression, data):
    """Select2 javaScript generator"""
    lines = []
    append = lines.append
    for key, value in list(data.items()):
        # apply functions
        if value is None:
            continue
        elif value is True:
            append("\n    %s: true" % key)
        elif value is False:
            append("\n    %s: false" % key)
        elif value is NULL:
            append("\n    %s: null" % key)
        elif key in [
            'language',
            'dropdownCss',
            'containerCss',
            ]:
            l = ["      %s: %s" % (k,v) for k,v in list(value.items())]
            if l:
                append("\n    %s: {\n%s\n    }" % (key, ',\n'.join(l)))
        elif key in [
            'tokenSeparators',
            ]:
            v = [str(v) for v in list(value)]
            append("\n    %s: %s" % (key, v))
        elif key in [
            'ajax',
            'createTag',
            'data',
            'dataAdapter',
            'dropdownParent',
            'escapeMarkup',
            'insertTag',
            'matcher',
            'resultsAdapter',
            'selectionAdapter',
            'sorter',
            'tags',
            'templateResult',
            'templateSelection',
            ]:
            append("\n    %s: %s" % (key, value))
        elif isinstance(value, (list, int)):
            append("\n    %s: %s" % (key, value))
        elif isinstance(value, six.string_types):
            if value.startswith('$'):
                append("\n    %s: %s" % (key, value))
            else:
                append("\n    %s: '%s'" % (key, value))
        else:
            append("\n    %s: %s" % (key, value))
    code = ','.join(lines)
    return j01_select2_template % (widgetExpression, code)


INPUT_TOO_SHORT = """function (args) {
          var nChars = args.minimum - args.input.length;
          return "%s";
        }"""

INPUT_TOO_LONG = """function (args) {
          var nChars = args.input.length - args.maximum;
          return "%s";
        }"""


##############################################################################
#
# select widget base class

class Select2WidgetMixin(object):
    """Selects input widget"""

    # you can override this in your custom widget factory
    klass = u'j01Select2Widget'
    css = u'j01-select2'

    multiple = 'multiple'

    width = '100%'

    # select2 properties (see https://select2.org/configuration/options-api)
    # None means default value
    # NULL means null
    adaptContainerCssClass = None
    adaptDropdownCssClass = None
    allowClear = None
    closeOnSelect = None                # True
    containerCss = None
    containerCssClass = None
    data = None
    dataAdapter = None #'J01Data'
    debug = None
    disabled = None
    dropdownAdapter = None
    dropdownAutoWidth = None
    dropdownCss = None
    dropdownCssClass = None
    dropdownParent = None
    escapeMarkup = None

    matcher = None
    maximumInputLength = None
    maximumSelectionLength = None
    minimumInputLength = None
    minimumResultsForSearch = 10

    placeholder = None
    resultsAdapter = None
    selectionAdapter = None
    selectOnClose = None                # False
    sorter = None

    tags = None
    createTag = None
    insertTag = None

    templateResult = None
    templateSelection = None
    theme = None

    tokenizer = None
    tokenSeparators = None
    scrollAfterSelect = None

    ajax = None

    def translate(self, msg, default=None):
        if default is None:
            default = msg
        return zope.i18n.translate(msg, context=self.request, default=default)

    # i18n properties
    @property
    def formatErrorLoading(self):
        msg = self.translate(_("The results could not be loaded."))
        return 'function() {return "%s";}' % msg

    @property
    def formatInputTooLong(self):
        msg = self.translate(_(
            u'Please delete $nChars characters',
            mapping={'nChars': '"+nChars+"'}))
        return INPUT_TOO_LONG % msg

    @property
    def formatInputTooShort(self):
        msg = self.translate(_(
            u'Please enter $nChars or more characters',
            mapping={'nChars': '"+nChars+"'}))
        return INPUT_TOO_SHORT % msg

    @property
    def formatLoadMore(self):
        msg = self.translate(_('Loading more results...'))
        return 'function() {return "%s";}' % msg

    @property
    def formatMaximumSelected(self):
        msg = self.translate(_(
            u'You can only select $nChars item',
            mapping={'nChars': '"+ args.maximum +"'}))
        return 'function(args) {return "%s";}' % msg

    @property
    def formatNoResults(self):
        msg = self.translate(_("No results found"))
        return 'function() {return "%s";}' % msg

    @property
    def formatSearching(self):
        msg = self.translate(_("Searching..."))
        return 'function() {return "%s";}' % msg

    @property
    def formatRemoveAllItems(self):
        msg = self.translate(_('Remove all items'))
        return 'function() {return "%s";}' % msg

    @property
    def language(self):
        return {
            'errorLoading': self.formatErrorLoading,
            'inputTooLong': self.formatInputTooLong,
            'inputTooShort': self.formatInputTooShort,
            'loadingMore': self.formatLoadMore,
            'maximumSelected': self.formatMaximumSelected,
            'noResults': self.formatNoResults,
            'searching': self.formatSearching,
            'removeAllItems': self.formatRemoveAllItems,
        }

    def getDataAdapter(self):
        return self.dataAdapter

    def getPlaceholder(self):
        placeholder = self.placeholder
        if placeholder is not None:
            return self.translate(placeholder)

    @property
    def settings(self):
        dataAdapter = self.getDataAdapter()
        placeholder = self.getPlaceholder()
        return {
            'adaptContainerCssClass': self.adaptContainerCssClass,
            'adaptDropdownCssClass': self.adaptDropdownCssClass,
            'allowClear': self.allowClear,
            'closeOnSelect': self.closeOnSelect,
            'containerCss': self.containerCss,
            'containerCssClass': self.containerCssClass,
            'data': self.data,
            'dataAdapter': dataAdapter,
            'debug': self.debug,
            'disabled': self.disabled,
            'dropdownAdapter': self.dropdownAdapter,
            'dropdownAutoWidth': self.dropdownAutoWidth,
            'dropdownCss': self.dropdownCss,
            'dropdownCssClass': self.dropdownCssClass,
            'dropdownParent': self.dropdownParent,
            'escapeMarkup': self.escapeMarkup,

            'matcher': self.matcher,
            'maximumInputLength': self.maximumInputLength,
            'maximumSelectionLength': self.maximumSelectionLength,
            'minimumInputLength': self.minimumInputLength,
            'minimumResultsForSearch': self.minimumResultsForSearch,

            'placeholder': placeholder,
            'resultsAdapter': self.resultsAdapter,
            'selectionAdapter': self.selectionAdapter,
            'selectOnClose': self.selectOnClose,
            'sorter': self.sorter,
            'tags': self.tags,

            'templateResult': self.templateResult,
            'templateSelection': self.templateSelection,
            'theme': self.theme,

            'tokenizer': self.tokenizer,
            'tokenSeparators': self.tokenSeparators,
            'width': self.width,
            'scrollAfterSelect': self.scrollAfterSelect,

            'language': self.language,

            'ajax': self.ajax,
           }

    @property
    def javascript(self):
        return j01Select2JavaScript(self.id, self.settings)


class Select2WidgetBase(Select2WidgetMixin):
    """Select widget for IChoice or IList of IChoice fields base class"""

    noValueToken = '--NOVALUE--'

    prompt = False

    noValueMessage = _('No value')
    promptMessage = _('Select a value ...')

    # Internal attributes
    _adapterValueAttributes = \
        z3c.form.widget.SequenceWidget._adapterValueAttributes + \
        ('noValueMessage', 'promptMessage', 'prompt')

    def isSelected(self, term):
        return term.token in self.value

    def isGroupTerm(self, term):
        return getattr(term, 'isGroup', False)

    def getTermTitle(self, term):
        """Return option term title"""
        if zope.schema.interfaces.ITitledTokenizedTerm.providedBy(term):
            return self.translate(term.title)
        elif term.title:
            return self.translate(term.title)
        else:
            return term.token

    def getGroupTermTitle(self, term):
        """Return option group term title"""
        return self.getTermTitle(term)

    @property
    def displayValue(self):
        res = []
        append = res.append
        for token in self.value:
            # Ignore no value entries. They are in the request only.
            if token == self.noValueToken:
                continue
            try:
                term = self.terms.getTermByToken(token)
                value = self.getTermTitle(term)
                append(value)
            except LookupError:
                # silently ignore missing tokens, because INPUT_MODE and
                # HIDDEN_MODE does that too
                continue
        return res

    @property
    def items(self):
        """Returns items supporting optional optgroups"""
        if self.terms is None:
            # update() has not been called yet
            return ()
        idx = 0
        items = []
        if (not self.required or self.prompt) and self.multiple is None:
            message = self.noValueMessage
            if self.prompt:
                message = self.promptMessage
            items.append({
                'isGroup': False,
                'id': self.id + '-novalue',
                'value': self.noValueToken,
                'content': message,
                'isGroup': False,
                'selected': self.value == []
                })

        ignored = set(self.value)

        def addOption(idx, term, items, prefix=''):
            selected = self.isSelected(term)
            if selected and term.token in ignored:
                ignored.remove(term.token)
            content = self.getTermTitle(term)
            idx += 1
            items.append({
                'id': '%s-%s%i' % (self.id, prefix, idx),
                'value': term.token,
                'content': content,
                'isGroup': False,
                'selected': selected,
                })
            return idx

        def addOptGroup(idx, gName, items, subTerms):
            """Append collected sub terms as optgroup subItems"""
            subItems = []
            for subTerm in subTerms:
                idx = addOption(idx, subTerm, subItems)
            items.append({
                'isGroup': True,
                'content': gName,
                'subItems': subItems,
                })
            return idx

        # setup optgroup and option items
        gName = None
        subTerms = []
        for _, term in enumerate(self.terms):
            if self.isGroupTerm(term):
                if gName is not None and subTerms:
                    idx = addOptGroup(idx, gName, items, subTerms)
                     # set empty subTerms list
                    subTerms = []
                # set as next gName
                gName = self.getGroupTermTitle(term)
            else:
                # collect sub item terms
                subTerms.append(term)

        # render the last collected sub terms with the latest gName
        if gName is not None:
            idx = addOptGroup(idx, gName, items, subTerms)
        elif subTerms:
            for _, term in enumerate(subTerms):
                idx = addOption(idx, term, items)
        if ignored:
            # some values are not displayed, probably they went away from the
            # source/vocabulary
            for _, token in enumerate(sorted(ignored)):
                try:
                    term = self.terms.getTermByToken(token)
                except LookupError:
                    # just in case the term really went away
                    continue
                idx = addOption(idx, term, items, prefix='missing-')

        return items


@zope.interface.implementer_only(interfaces.ISelect2Widget)
class Select2Widget(Select2WidgetBase,z3c.form.browser.widget.HTMLSelectWidget,
    z3c.form.widget.SequenceWidget):
    """Select widget for IList of IChoice fields

    - all values must be a part of the choice vocabulary/source

    - No custom input is allowed

    - The widget will render the result as select input element

    - multiple values are allowed as input. You can set the amount of
      allowed input with the maximumInputLength property

    """


    multiple = 'multiple'


@zope.interface.implementer_only(interfaces.ISingleSelect2Widget)
class SingleSelect2Widget(Select2WidgetBase,
    z3c.form.browser.widget.HTMLSelectWidget, z3c.form.widget.SequenceWidget):
    """Select widget for IChoice fields

    - all values must be a part of the choice vocabulary/source

    - No custom input is allowed

    - The widget will render the result as select input element

    - only a single value is allowed

    """


    multiple = None


################################################################################
#
# helper mixin classes (not used in our widgets, but usable in other use cases)

class WidgetItemsMixin(object):
    """Widget items mixin class

    This miin class will render select element items used in the widget
    template based on the source. The items method supports optgroup if
    you use a group vocabulary/source providing terms with an isGroup attribute.
    """

    source = None
    prompt = False

    termAttrName = 'title'

    noValueToken = '--NOVALUE--'

    noValueMessage = _('No value')
    promptMessage = _('Select a value ...')

    # Internal attributes
    _adapterValueAttributes = z3c.form.widget.Widget._adapterValueAttributes + \
        ('noValueMessage', 'promptMessage', 'prompt')

    def getVocabulary(self):
        """Setup translated vocabulary source as terms

        HEADSUP: Ths getTerms method is a p01.vocabulary specific
        implementation optimised for pre translates and cached vocabularies.
        You probably need to replace the getTerms method and you your
        own source/vocabulary lookup concept.
        """
        if self.source is not None:
            return self.source.getVocabulary(request=self.request)

    def isSelected(self, term):
        return getattr(term, self.termAttrName, None) in self.value

    def isGroupTerm(self, term):
        return getattr(term, 'isGroup', False)

    def getOptionValue(self, term):
        """Returns the option value from a given term (token by default)"""
        return getattr(term, self.termAttrName, None)

    @property
    def items(self):
        """Returns items supporting optional optgroups"""
        vocab = self.getVocabulary()
        idx = 0
        items = []
        if vocab is None:
            return items
        # we use placeholder instead of no value term
        # if (not self.required or self.prompt) and self.multiple is None:
        #     message = self.noValueMessage
        #     if self.prompt:
        #         message = self.promptMessage
        #     items.append({
        #         'id': self.id + '-novalue',
        #         'value': self.noValueToken,
        #         'content': message,
        #         'isGroup': False,
        #         'selected': self.value == []
        #         })

        ignored = set(self.value)

        def addOption(idx, term, items, prefix=''):
            selected = self.isSelected(term)
            v = self.getOptionValue(term)
            if selected and v in ignored:
                ignored.remove(v)
            idx += 1
            items.append({
                'id': '%s-%s%i' % (self.id, prefix, idx),
                'value': self.getOptionValue(term),
                'content': term.title,
                'isGroup': False,
                'selected': selected,
                })
            return idx

        def addOptGroup(idx, gName, items, subTerms):
            """Append collected sub terms as optgroup subItems"""
            subItems = []
            for subTerm in subTerms:
                idx = addOption(idx, subTerm, subItems)
            items.append({
                'isGroup': True,
                'content': gName,
                'subItems': subItems,
                })
            return idx

        # setup optgroup and option items
        gName = None
        subTerms = []
        for term in vocab:
            if self.isGroupTerm(term):
                if gName is not None and subTerms:
                    idx = addOptGroup(idx, gName, items, subTerms)
                     # set empty subTerms list
                    subTerms = []
                # set as next gName
                gName = term.title
            else:
                # collect sub item terms
                subTerms.append(term)

        # render the last collected sub terms with the latest gName
        if gName is not None:
            idx = addOptGroup(idx, gName, items, subTerms)
        elif subTerms:
            for _, term in enumerate(subTerms):
                idx = addOption(idx, term, items)
        if ignored:
            # some values are not displayed, probably they went away from the
            # source/vocabulary
            for _, v in enumerate(sorted(ignored)):
                try:
                    if self.attrName == 'value':
                        term = vocab.getTerm(v)
                    elif self.attrName == 'title':
                        term = vocab.queryTermByTitle(v)
                    else:
                        term = vocab.getTermByToken(v)
                    idx = addOption(idx, term, items)
                except (AttributeError, LookupError):
                    # that's custom text input
                    idx += 1
                    items.append({
                        'id': '%s-%i' % (self.id, idx),
                        'value': v,
                        'content': v,
                        'isGroup': False,
                        'selected': True,
                        })
        return items


class WidgetDataValueMixin(object):
    """Widget data mixin class

    NOTE: this is just a sample implementation describing how you can render
    selected values. This mixin class will force to render existing values
    as select option. You can probably use this mixin class in your custom
    LiveListSelect2 or LiveTagSelect2Widget widget. Remember, the widget
    is initial empty providing a text input. The user can then search for
    terms and the implementation will lookup for additional values rendered as
    options.
    """

    source = None

    @property
    def items(self):
        """Select element items will get renered by the data attribute"""
        return []

    def getVocabulary(self):
        """Returns a translated vocabulary source

        HEADSUP: Ths getVocabulary method is a p01.vocabulary specific
        implementation optimised for pre translates and cached vocabularies.
        You probably need to replace the getVocabulary method and you your
        own source/vocabulary lookup concept.
        """
        if self.source is not None:
            return self.source.getVocabulary(request=self.request)

    def getData(self):
        """Returns data tokens"""
        res = []
        append = res.append
        vocab = self.getVocabulary()
        if vocab is not None and self.value:
            # append existing values
            for token in self.value:
                term = vocab.getTermByToken(token)
                append({'id': term.token, 'text': term.title})
        return res

    @property
    def data(self):
        """Retruns existing value as select2 data used by javascript"""
        res = []
        append = res.append
        for data in self.getData():
            append('{"id": "%s", "text": "%s", selected: true}' % (
                data['id'], data['text']))
        if res:
            return "[%s]" % ",".join(res)
        else:
            # can provide initial value, "null" means no value
            return "null"


################################################################################
#
# adapter and optional jsonrpc lookup widget

AJAX = """{
    data: function(params) {
        var query = $.extend({page: 1}, params);
        return {
            term: query.term,
            page: query.page
        }
    },
    processResults: function(data) {
        return data
    },
    transport: function(params, success, failure) {
        var data = params.data;
        var proxy = getJSONRPCProxy('%(j01Select2URL)s');
        proxy.addMethod('%(j01Select2MethodName)s', success, failure, 'j01Select2');
        proxy.%(j01Select2MethodName)s(data);
        return proxy;
    }
}
"""

class WidgetDataMixin(object):
    """Widget data attribute mixin class

    This mixin class can get used for rendering options based on a vocabulary
    source and is using the data attribute without using the items/terms lookup
    for renering the option and optgroup items in the select widget.

    Implement the a JSONRPCMethod as shown below for supporting aditional data
    lookup via jsonrpc and register the method with a name.

    Define the name as j01Select2MethodName and the built-in ajax attribute
    will use a generic call to the jsonrpc method fo lookup additional
    option values.

    Such a JSONRPCMethod must return the following data for rendering options.

    {
        "results": [
            {"id": "mytag", text: "mytag" },
            { "id": "another", text: "another" }
        ],
        "pagination": {
            "more": false
        }
    }

    {
        results: [{
            text: "Western",
            "children": [
                {"id": "CA", text: "California" },
                {"id": "AZ", text: "Arizona", "selected": true}
            ]},{
            "text": "Eastern",
            "children": [
                {"id": "FL", text: "Florida"}
            ]}
        ],
        "pagination": {
            "more": false
        }
    }

    NOTE: if you set more = True, the search result will load new data on
    scrolling to the end. This means you to return more=False or there must
    new data where we can fetch.

    NOTE: return the search term too if you like to offer text input,
    otherwise the given term is not selectable as input in the
    result.

    NOTE: you probably need to implement your own search lookup and return
    one or more values based on the search string. This sample will only
    mirror the given search text as input which is probably useless. Or
    this is also supported by the SingleTagSelect2Widget or
    TagListSelect2Widget with the attribute tags=tue without a server roundtrip.

    Such a sample JSONRPCMethod looks like:

    def getSampleResult(self, term, page):
        term = term.strip()
        more = False
        # return the serach string or we will miss that term in our result
        results = [{"id": term+"1", "text": term}]
        return {"pagination": {"more": more}, "results": results}

    And your widget has to define the j01Select2MethodName attribute like:

    j01Select2MethodName = 'getSampleResult'

    """

    source = None

    noValueToken = '--NOVALUE--'

    optGroupTitleCustom = _(u"Additional selection")

    j01Select2MethodName = None

    @property
    def j01Select2URL(self):
        return absoluteURL(self.form, self.request)

    def getDataAdapter(self):
        return None

    @property
    def ajax(self):
        if self.j01Select2MethodName is not None:
            # simple jsonrpc method usage
            return AJAX % {
                'j01Select2URL': self.j01Select2URL,
                'j01Select2MethodName': self.j01Select2MethodName,
            }

    @property
    def items(self):
        """Select element items will get renered by the data attribute"""
        return []

    def getVocabulary(self):
        """Setup translated vocabulary source as terms

        HEADSUP: Ths getTerms method is a p01.vocabulary specific
        implementation optimised for pre translates and cached vocabularies.
        You probably need to replace the getTerms method and you your
        own source/vocabulary lookup concept.
        """
        if self.source is not None:
            return self.source.getVocabulary(request=self.request)

    def isGroupTerm(self, term):
        return getattr(term, 'isGroup', False)

    def isSelected(self, term):
        return term.title in self.value

    @property
    def displayValue(self):
        value = []
        vocab = self.getVocabulary()
        if vocab is not None:
            for token in self.value:
                # Ignore no value entries. They are in the request only.
                if token == self.noValueToken:
                    continue
                try:
                    term = vocab.getTermByToken(token)
                except LookupError:
                    # silently ignore missing tokens, because INPUT_MODE and
                    # HIDDEN_MODE does that too
                    continue
                if zope.schema.interfaces.ITitledTokenizedTerm.providedBy(term):
                    value.append(self.translate(term.title))
                else:
                    value.append(term.value)
        else:
            vallue = self.value
        return value

    @property
    def data(self):
        """Data
        NOTE: group vocabulary MUST start with a group. Group vocabulary NOT
        starting with a group are not supported yet and the terms will get
        rendered without groups.
        """
        vocab = self.getVocabulary()
        if vocab is not None:
            group = None
            terms = []
            children = []

            if self.value:
                ignored = set(self.value)
            else:
                ignored = set()

            for term in vocab:
                # vocabulary starting with a group
                if self.isGroupTerm(term):
                    if group is not None:
                        # add group to terms
                        terms.append(
                            '{"text": "%s", "children": [%s]}' % (
                                group, ",".join(children))
                        )
                    # setup new group
                    group = term.title
                    children = []
                else:
                    if term.title in ignored:
                        ignored.remove(term.title)
                    if self.isSelected(term):
                        d = '{"id": "%s", "text": "%s", "selected": true}' % (
                            term.title, term.title)
                    else:
                        d = '{"id": "%s", "text": "%s"}' % (term.title,
                            term.title)
                    children.append(d)
            if group is not None:
                # add latest group and children to terms
                terms.append(
                    '{"text": "%s", "children": [%s]}' % (
                        group, ",".join(children))
                )
            else:
                # no groups, use all children as terms
                terms = children
            if ignored:
                # add custom text input not contained in vocab
                if group is None:
                    # append them to children
                    for v in ignored:
                        d = '{"id": "%s", "text": "%s", "selected": true}' % (
                            v, v)
                        terms.append(d)
                else:
                    # append a group for custm items
                    group = self.translate(self.optGroupTitleCustom)
                    children = []
                    for v in ignored:
                        d = '{"id": "%s", "text": "%s", "selected": true}' % (
                            v, v)
                        children.append(d)
                    terms.append(
                        '{"text": "%s", "children": [%s]}' % (
                            group, ",".join(children))
                    )

            return "[%s]" % ",".join(terms)
        else:
            # retun existing values as tokens
            terms = []
            if self.value:
                for value in self.value:
                    d = '{"id": "%s", "text": "%s", "selected": true}' % (
                        value, value)
                    terms.append(d)
            return "[%s]" % ",".join(terms)


@zope.interface.implementer_only(interfaces.ISingleTagSelect2Widget)
class SingleTagSelect2Widget(WidgetDataMixin, Select2WidgetMixin,
    z3c.form.browser.text.TextWidget):
    """Widget for ITextLine

    This widget is based on a ITextLine field, this means we can enter
    custom text data and the JSON-RPC callback is used for autosuggest
    useable input.

    NOTE; this widget can only set one tag and not a list of tags.

    You can offer initial data and JSON-RPC autosuggest values.

    """


    # tags are allways multiple but limited with maximumSelectionLength
    multiple = 'multiple'
    # single token restriction
    maximumSelectionLength = 1
    minimumInputLength = 1

    # allows custom text input
    tags = True
    # force rendering as token
    tokenSeparators = []


@zope.interface.implementer_only(interfaces.ITagListSelect2Widget)
class TagListSelect2Widget(WidgetDataMixin, Select2WidgetMixin,
    z3c.form.browser.text.TextWidget):
    """Widget for IList of ITextLine

    This widget is based on a IList of ITextLine field, this means we can enter
    custom text data and the JSON-RPC callback is used for autosuggest
    useable input.

    """


    multiple = 'multiple'

    tags = True
    tokenSeparators = [',', ' ']
    minimumInputLength = 1


################################################################################
#
# jsonrpc lookup widget

class LiveListTermsSelect2WidgetBase(Select2WidgetBase):
    """JSONRPC mixin class"""

    # use our default widget field lookup method called j01Select2Result
    # which is using the built in getSelect2Result method.
    j01Select2MethodName = 'j01Select2Result'

    @property
    def dummyValue(self):
        # forces to invoke initSelection, an empty value prevents
        return self.noValueToken

    def extract(self, default=NO_VALUE):
        """See z3c.form.interfaces.IWidget

        You probably need to implement a custom extract method which will
        fit for extracting the value in your implementation.
        """
        if (self.name not in self.request and
            self.name+'-empty-marker' in self.request):
            return []
        value = self.request.get(self.name, default)
        if value != default:
            if isinstance(value, six.string_types):
                # extract widget value and split by separator. If the value
                # is not a base string, it was set during form setup
                value = value.split(self.separator)
            # do some kind of validation, at least only use existing values
            for token in value:
                if token == self.noValueToken:
                    continue
                try:
                    # does this value exist?
                    self.terms.getTermByToken(token)
                except LookupError:
                    return default
        return value

    @property
    def j01Select2URL(self):
        return absoluteURL(self.form, self.request)

    def getSelect2Result(self, fieldName, searchString, page):
        """Search for new tags based on search string

        The result should look like:

        {
            "results": [
                {"id": "mytag", text: "mytag" },
                { "id": "another", text: "another" }
            ],
            "pagination": {
                "more": false
            }
        }

        or if you like to support select widget optgroup option grouping:

        {
            results: [{
                text: "Western",
                "children": [
                    {"id": "CA", text: "California" },
                    {"id": "AZ", text: "Arizona", "selected": true}
                ]},{
                "text": "Eastern",
                "children": [
                    {"id": "FL", text: "Florida"}
                ]}
            ],
            "pagination": {
                "more": false
            }
        }
        """
        terms = self.terms.terms.search(searchString, page, self.size)
        page = terms.page
        pages = terms.pages
        more = terms.more
        groupName = None
        children = []
        results = []
        append = results.append
        for term in terms:
            if term.groupName is None:
                # add term data without using groups
                append({
                    "id": term.token,
                    "text": term.title,
                    })
            elif groupName is None:
                # start with initial group
                groupName = term.groupName
                children = []
                children.append({
                    "id": term.token,
                    "text": term.title,
                    })
            elif term.groupName != groupName:
                # add children with previous groupName to result
                append({
                    "text": groupName,
                    "children": children,
                    })
                # start with next group
                groupName = term.groupName
                children = []
                children.append({
                    "id": term.token,
                    "text": term.title,
                    })
        return {
            "pagination": {"more": more},
            "results": results,
            }


################################################################################
#
# live list source widget

@zope.interface.implementer_only(interfaces.ILiveTagSelect2Widget)
class LiveTagSelect2Widget(LiveListTermsSelect2WidgetBase,
    z3c.form.browser.widget.HTMLTextInputWidget,
    z3c.form.widget.SequenceWidget):
    """Widget for IChoice"""


    size = 25
    minimumInputLength = 2


@zope.interface.implementer_only(interfaces.ILiveListSelect2Widget)
class LiveListSelect2Widget(LiveListTermsSelect2WidgetBase,
    z3c.form.browser.widget.HTMLTextInputWidget,
    z3c.form.widget.SequenceWidget):
    """Widget for IList of IChoice

    This more or less generic implementation uses ILiveListSource and the api
    defined in the interface ILiveListSource. But you probably will implement
    a simpler and faster source and value lookup concept in your custom
    implementation. The methods below will contain a sample result format.
    """


    size = 25
    minimumInputLength = 2
    # custom input is allowed
    tags = True


################################################################################
#
# HTML select element
@zope.interface.implementer(IFieldWidget)
def getSelect2Widget(field, request):
    """IFieldWidget factory for Select2Widget."""
    return z3c.form.widget.FieldWidget(field, Select2Widget(request))


@zope.interface.implementer(IFieldWidget)
def getPromptSelect2Widget(field, request):
    """IFieldWidget factory for Select2Widget."""
    widget = z3c.form.widget.FieldWidget(field, Select2Widget(request))
    widget.prompt = True
    return widget


@zope.interface.implementer(IFieldWidget)
def getSingleSelect2Widget(field, request):
    """IFieldWidget factory for Select2Widget."""
    widget = z3c.form.widget.FieldWidget(field, Select2Widget(request))
    widget.multiple = None
    return widget


@zope.interface.implementer(IFieldWidget)
def getPromptSingleSelect2Widget(field, request):
    """IFieldWidget factory for Select2Widget."""
    widget = z3c.form.widget.FieldWidget(field, Select2Widget(request))
    widget.prompt = True
    widget.multiple = None
    return widget


# tagging with getVocabulary and jsonrpc

@zope.interface.implementer(IFieldWidget)
def getSingleTagSelect2Widget(field, request):
    """IFieldWidget factory for LiveListSelect2Widget."""
    return z3c.form.widget.FieldWidget(field, SingleTagSelect2Widget(request))

def setUpSingleTagSelect2Widget(source, **kwargs):
    def inner(field, request):
        widget = getSingleTagSelect2Widget(field, request)
        widget.source = source
        for k,v in list(kwargs.items()):
            setattr(widget, k, v)
        return widget
    return inner


@zope.interface.implementer(IFieldWidget)
def getTagListSelect2Widget(field, request):
    """IFieldWidget factory for TagListSelect2Widget."""
    return z3c.form.widget.FieldWidget(field, TagListSelect2Widget(request))

def setUpTagListSelect2Widget(source, **kwargs):
    def inner(field, request):
        widget = getTagListSelect2Widget(field, request)
        widget.source = source
        for k,v in list(kwargs.items()):
            setattr(widget, k, v)
        return widget
    return inner

# tagging using terms and jsonrpc

@zope.interface.implementer(IFieldWidget)
def getLiveListSelect2Widget(field, request):
    """IFieldWidget factory for LiveListSelect2Widget."""
    return z3c.form.widget.FieldWidget(field, LiveListSelect2Widget(request))

@zope.interface.implementer(IFieldWidget)
def getLiveTagSelect2Widget(field, request):
    """IFieldWidget factory for LiveListSelect2Widget."""
    return z3c.form.widget.FieldWidget(field, LiveTagSelect2Widget(request))