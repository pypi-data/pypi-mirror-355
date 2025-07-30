#======
#README
#======

#Let's test the source code with our custom checker:

from __future__ import unicode_literals
from __future__ import absolute_import
import p01.checker#>>>
import j01.select2#>>>

skipFileNames = [#>>>
    'j01Select2.png',#...
    'j01Select2Spinner.gif',#...
    'j01Select2x2.png',#...
]#...

skipFolderNames = [#>>>
]#...

checker = p01.checker.Checker()#>>>
checker.check(j01.select2, skipFileNames=skipFileNames,#>>>
    skipFolderNames=skipFolderNames)#...
#  -------------------
#  css/j01.select2.css
#  -------------------
#  136: Unknown property 'clip-path'.
#        clip-path: inset(50%) !important;
