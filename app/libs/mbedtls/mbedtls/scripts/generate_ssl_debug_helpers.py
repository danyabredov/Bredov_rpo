#!/usr/bin/env python3

"""Generate library/ssl_debug_helps_generated.c

The code generated by this module includes debug helper functions that can not be
implemented by fixed codes.

"""

# Copyright The Mbed TLS Contributors
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import re
import os
import textwrap
import argparse
from mbedtls_dev import build_tree


def remove_c_comments(string):
    """
        Remove C style comments from input string
    """
    string_pattern = r"(?P<string>\".*?\"|\'.*?\')"
    comment_pattern = r"(?P<comment>/\*.*?\*/|//[^\r\n]*$)"
    pattern = re.compile(string_pattern + r'|' + comment_pattern,
                         re.MULTILINE | re.DOTALL)

    def replacer(match):
        if match.lastgroup == 'comment':
            return ""
        return match.group()
    return pattern.sub(replacer, string)


class CondDirectiveNotMatch(Exception):
    pass


def preprocess_c_source_code(source, *classes):
    """
        Simple preprocessor for C source code.

        Only processses condition directives without expanding them.
        Yield object according to the classes input. Most match firstly

        If the directive pair does not match , raise CondDirectiveNotMatch.

        Assume source code does not include comments and compile pass.

    """

    pattern = re.compile(r"^[ \t]*#[ \t]*" +
                         r"(?P<directive>(if[ \t]|ifndef[ \t]|ifdef[ \t]|else|endif))" +
                         r"[ \t]*(?P<param>(.*\\\n)*.*$)",
                         re.MULTILINE)
    stack = []

    def _yield_objects(s, d, p, st, end):
        """
            Output matched source piece
        """
        nonlocal stack
        start_line, end_line = '', ''
        if stack:
            start_line = '#{} {}'.format(d, p)
            if d == 'if':
                end_line = '#endif /* {} */'.format(p)
            elif d == 'ifdef':
                end_line = '#endif /* defined({}) */'.format(p)
            else:
                end_line = '#endif /* !defined({}) */'.format(p)
        has_instance = False
        for cls in classes:
            for instance in cls.extract(s, st, end):
                if has_instance is False:
                    has_instance = True
                    yield pair_start, start_line
                yield instance.span()[0], instance
        if has_instance:
            yield start, end_line

    for match in pattern.finditer(source):

        directive = match.groupdict()['directive'].strip()
        param = match.groupdict()['param']
        start, end = match.span()

        if directive in ('if', 'ifndef', 'ifdef'):
            stack.append((directive, param, start, end))
            continue

        if not stack:
            raise CondDirectiveNotMatch()

        pair_directive, pair_param, pair_start, pair_end = stack.pop()
        yield from _yield_objects(source,
                                  pair_directive,
                                  pair_param,
                                  pair_end,
                                  start)

        if directive == 'endif':
            continue

        if pair_directive == 'if':
            directive = 'if'
            param = "!( {} )".format(pair_param)
        elif pair_directive == 'ifdef':
            directive = 'ifndef'
            param = pair_param
        else:
            directive = 'ifdef'
            param = pair_param

        stack.append((directive, param, start, end))
    assert not stack, len(stack)


class EnumDefinition:
    """
        Generate helper functions around enumeration.

        Currently, it generate translation function from enum value to string.
        Enum definition looks like:
        [typedef] enum [prefix name] { [body] } [suffix name];

        Known limitation:
        - the '}' and ';' SHOULD NOT exist in different macro blocks. Like
        ```
        enum test {
            ....
        #if defined(A)
            ....
        };
        #else
            ....
        };
        #endif
        ```
    """

    @classmethod
    def extract(cls, source_code, start=0, end=-1):
        enum_pattern = re.compile(r'enum\s*(?P<prefix_name>\w*)\s*' +
                                  r'{\s*(?P<body>[^}]*)}' +
                                  r'\s*(?P<suffix_name>\w*)\s*;',
                                  re.MULTILINE | re.DOTALL)

        for match in enum_pattern.finditer(source_code, start, end):
            yield EnumDefinition(source_code,
                                 span=match.span(),
                                 group=match.groupdict())

    def __init__(self, source_code, span=None, group=None):
        assert isinstance(group, dict)
        prefix_name = group.get('prefix_name', None)
        suffix_name = group.get('suffix_name', None)
        body = group.get('body', None)
        assert prefix_name or suffix_name
        assert body
        assert span
        # If suffix_name exists, it is a typedef
        self._prototype = suffix_name if suffix_name else 'enum ' + prefix_name
        self._name = suffix_name if suffix_name else prefix_name
        self._body = body
        self._source = source_code
        self._span = span

    def __repr__(self):
        return 'Enum({},{})'.format(self._name, self._span)

    def __str__(self):
        return repr(self)

    def span(self):
        return self._span

    def generate_translation_function(self):
        """
            Generate function for translating value to string
        """
        translation_table = []

        for line in self._body.splitlines():

            if line.strip().startswith('#'):
                # Preprocess directive, keep it in table
                translation_table.append(line.strip())
                continue

            if not line.strip():
                continue

            for field in line.strip().split(','):
                if not field.strip():
                    continue
                member = field.strip().split()[0]
                translation_table.append(
                    '{space}[{member}] = "{member}",'.format(member=member,
                                                             space=' '*8)
                )

        body = textwrap.dedent('''\
            const char *{name}_str( {prototype} in )
            {{
                const char * in_to_str[]=
                {{
            {translation_table}
                }};

                if( in > ( sizeof( in_to_str )/sizeof( in_to_str[0]) - 1 ) ||
                    in_to_str[ in ] == NULL )
                {{
                    return "UNKOWN_VAULE";
                }}
                return in_to_str[ in ];
            }}
                    ''')
        body = body.format(translation_table='\n'.join(translation_table),
                           name=self._name,
                           prototype=self._prototype)
        return body

class SignatureAlgorithmDefinition:
    """
        Generate helper functions for signature algorithms.

        It generates translation function from signature algorithm define to string.
        Signature algorithm definition looks like:
        #define MBEDTLS_TLS1_3_SIG_[ upper case signature algorithm ] [ value(hex) ]

        Known limitation:
        - the definitions SHOULD  exist in same macro blocks.
    """

    @classmethod
    def extract(cls, source_code, start=0, end=-1):
        sig_alg_pattern = re.compile(r'#define\s+(?P<name>MBEDTLS_TLS1_3_SIG_\w+)\s+' +
                                     r'(?P<value>0[xX][0-9a-fA-F]+)$',
                                     re.MULTILINE | re.DOTALL)
        matches = list(sig_alg_pattern.finditer(source_code, start, end))
        if matches:
            yield SignatureAlgorithmDefinition(source_code, definitions=matches)

    def __init__(self, source_code, definitions=None):
        if definitions is None:
            definitions = []
        assert isinstance(definitions, list) and definitions
        self._definitions = definitions
        self._source = source_code

    def __repr__(self):
        return 'SigAlgs({})'.format(self._definitions[0].span())

    def span(self):
        return self._definitions[0].span()
    def __str__(self):
        """
            Generate function for translating value to string
        """
        translation_table = []
        for m in self._definitions:
            name = m.groupdict()['name']
            translation_table.append(
                '\tcase {}:\n\t    return "{}";'.format(name,
                                                        name[len('MBEDTLS_TLS1_3_SIG_'):].lower())
                )

        body = textwrap.dedent('''\
            const char *mbedtls_ssl_sig_alg_to_str( uint16_t in )
            {{
                switch( in )
                {{
            {translation_table}
                }};

                return "UNKOWN";
            }}''')
        body = body.format(translation_table='\n'.join(translation_table))
        return body

OUTPUT_C_TEMPLATE = '''\
/* Automatically generated by generate_ssl_debug_helpers.py. DO NOT EDIT. */

/**
 * \file ssl_debug_helpers_generated.c
 *
 * \brief Automatically generated helper functions for debugging
 */
/*
 *  Copyright The Mbed TLS Contributors
 *  SPDX-License-Identifier: Apache-2.0
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may
 *  not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

#include "common.h"

#if defined(MBEDTLS_DEBUG_C)

#include "ssl_debug_helpers.h"

{functions}

#endif /* MBEDTLS_DEBUG_C */
/* End of automatically generated file. */

'''


def generate_ssl_debug_helpers(output_directory, mbedtls_root):
    """
        Generate functions of debug helps
    """
    mbedtls_root = os.path.abspath(mbedtls_root or build_tree.guess_mbedtls_root())
    with open(os.path.join(mbedtls_root, 'include/mbedtls/ssl.h')) as f:
        source_code = remove_c_comments(f.read())

    definitions = dict()
    for start, instance in preprocess_c_source_code(source_code,
                                                    EnumDefinition,
                                                    SignatureAlgorithmDefinition):
        if start in definitions:
            continue
        if isinstance(instance, EnumDefinition):
            definition = instance.generate_translation_function()
        else:
            definition = instance
        definitions[start] = definition

    function_definitions = [str(v) for _, v in sorted(definitions.items())]
    if output_directory == sys.stdout:
        sys.stdout.write(OUTPUT_C_TEMPLATE.format(
            functions='\n'.join(function_definitions)))
    else:
        with open(os.path.join(output_directory, 'ssl_debug_helpers_generated.c'), 'w') as f:
            f.write(OUTPUT_C_TEMPLATE.format(
                functions='\n'.join(function_definitions)))


def main():
    """
    Command line entry
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--mbedtls-root', nargs='?', default=None,
                        help='root directory of mbedtls source code')
    parser.add_argument('output_directory', nargs='?',
                        default='library', help='source/header files location')

    args = parser.parse_args()

    generate_ssl_debug_helpers(args.output_directory, args.mbedtls_root)
    return 0


if __name__ == '__main__':
    sys.exit(main())
