# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Immutable data structures.

    Data structures which are completely immutable after creation. This
    behavior is useful for configuration objects, value objects, and other
    scenarios requiring collections with strong immutability guarantees.
'''


from . import __
# --- BEGIN: Injected by Copier ---
from . import exceptions
# --- END: Injected by Copier ---

from .classes import *
from .dictionaries import *
from .installers import *
from .modules import *
from .namespaces import *
from .sequences import *


__version__: __.typx.Annotated[ str, __.ddoc.Visibilities.Reveal ]
__version__ = '4.0'


__.ccstd.dynadoc.assign_module_docstring(
    __name__,
    introspection = __.dynadoc_introspection_control_on_package,
    table = __.fragments )
reclassify_modules( __name__, recursive = True )
