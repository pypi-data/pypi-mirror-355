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


''' Immutable namespaces.

    Provides a namespace type with immutable attributes. Similar to
    :py:class:`types.SimpleNamespace`, but attributes cannot be modified or
    deleted after initialization.

    The namespace implementation is modeled after
    :py:class:`types.SimpleNamespace` but adds immutability. Like
    :py:class:`types.SimpleNamespace`, it provides a simple ``__repr__`` which
    lists all attributes.

    >>> from frigid import Namespace
    >>> ns = Namespace( x = 1, y = 2 )
    >>> ns.z = 3  # Attempt to add attribute
    Traceback (most recent call last):
        ...
    frigid.exceptions.AttributeImmutability: Could not assign or delete attribute 'z'.
    >>> ns.x = 4  # Attempt modification
    Traceback (most recent call last):
        ...
    frigid.exceptions.AttributeImmutability: Could not assign or delete attribute 'x'.
    >>> ns
    frigid.namespaces.Namespace( x = 1, y = 2 )
''' # noqa: E501


from . import __
from . import classes as _classes


class Namespace( metaclass = _classes.Class ):
    # TODO: Dynadoc fragments.
    ''' Immutable namespaces. '''

    __slots__ = ( '__dict__', )

    def __init__(
        self,
        *iterables: __.DictionaryPositionalArgument[ __.H, __.V ],
        **attributes: __.DictionaryNominativeArgument[ __.V ],
    ) -> None:
        self.__dict__.update(
            __.ImmutableDictionary(
                *iterables, **attributes ) ) # pyright: ignore
        super( ).__init__( )

    def __repr__( self ) -> str:
        attributes = ', '.join(
            f"{key} = {value!r}" for key, value
            in getattr( self, '__dict__', { } ).items( ) )
        fqname = __.ccutils.qualify_class_name( type( self ) )
        if not attributes: return f"{fqname}( )"
        return f"{fqname}( {attributes} )"

    def __eq__( self, other: __.typx.Any ) -> __.ComparisonResult:
        if isinstance( other, ( Namespace, __.types.SimpleNamespace ) ):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__( self, other: __.typx.Any ) -> __.ComparisonResult:
        if isinstance( other, ( Namespace, __.types.SimpleNamespace ) ):
            return self.__dict__ != other.__dict__
        return NotImplemented
