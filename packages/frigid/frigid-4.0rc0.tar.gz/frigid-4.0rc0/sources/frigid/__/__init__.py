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


''' Common constants, imports, and utilities. '''


from .dictionaries import *
from .doctab import *
from .imports import *
from .nomina import *


dynadoc_introspection_limiter = (
    ccstd.dynadoc.produce_dynadoc_introspection_limiter(
        attributes_namer = calculate_attrname ) )
dynadoc_introspection_control_on_class = (
    ccstd.dynadoc.produce_dynadoc_introspection_control(
        limiters = ( dynadoc_introspection_limiter, ) ) )
dynadoc_introspection_control_on_package = (
    ccstd.dynadoc.produce_dynadoc_introspection_control(
        limiters = ( dynadoc_introspection_limiter, ),
        targets = ddoc.IntrospectionTargetsOmni ) )
