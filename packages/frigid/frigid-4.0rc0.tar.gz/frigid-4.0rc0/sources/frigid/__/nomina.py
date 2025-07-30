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


''' Common names and type aliases. '''

# ruff: noqa: F401


from classcore.standard.nomina import (
                            AttributesNamer,
                            BehaviorExclusionVerifiersOmni,
    DecorationPreparers as  ClassDecorationPreparers,
                            DynadocConfiguration,
                            concealment_label,
                            immutability_label,
)

from . import imports as __


H = __.typx.TypeVar( 'H', bound = __.cabc.Hashable )  # Hash Key
T = __.typx.TypeVar( 'T', bound = type ) # Class
U = __.typx.TypeVar( 'U' )  # Class
V = __.typx.TypeVar( 'V' )  # Value


ComparisonResult: __.typx.TypeAlias = bool | __.types.NotImplementedType
NominativeArguments: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
PositionalArguments: __.typx.TypeAlias = __.cabc.Sequence[ __.typx.Any ]

# TODO: Import ClassDecorator aliases from 'classcore' once documentation
#       fragments have been removed from them.
ClassDecorator: __.typx.TypeAlias = (
    __.cabc.Callable[ [ type[ U ] ], type[ U ] ] )
ClassDecorators: __.typx.TypeAlias = (
    __.cabc.Sequence[ ClassDecorator[ U ] ] )
ClassDecoratorFactory: __.typx.TypeAlias = (
    __.cabc.Callable[ ..., ClassDecorator[ U ] ] )

DictionaryNominativeArgument: __.typx.TypeAlias = __.typx.Annotated[
    V,
    __.ddoc.Doc(
        'Zero or more keyword arguments from which to initialize '
        'dictionary data.' ),
]
DictionaryPositionalArgument: __.typx.TypeAlias = __.typx.Annotated[
    __.cabc.Mapping[ H, V ] | __.cabc.Iterable[ tuple[ H, V ] ],
    __.ddoc.Doc(
        'Zero or more iterables from which to initialize dictionary data. '
        'Each iterable must be dictionary or sequence of key-value pairs. '
        'Duplicate keys will result in an error.' ),
]
DictionaryValidator: __.typx.TypeAlias = __.typx.Annotated[
    __.cabc.Callable[ [ H, V ], bool ],
    __.ddoc.Doc(
        'Callable which validates entries before addition to dictionary.' ),
]
ModuleReclassifier: __.typx.TypeAlias = __.cabc.Callable[
    [ __.cabc.Mapping[ str, __.typx.Any ] ], None ]


package_name = __name__.split( '.', maxsplit = 1 )[ 0 ]


def calculate_attrname( level: str, core: str ) -> str:
    return f"_{package_name}_{level}_{core}_"


def is_public_identifier( name: str ) -> bool:
    ''' Is Python identifier public? '''
    return not name.startswith( '_' )
