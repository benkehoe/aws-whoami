# Copyright 2020 Ben Kehoe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility for determining what AWS account and identity you're using."""

from __future__ import print_function

import argparse
from collections import namedtuple
import json
import sys
import os
import traceback

import botocore
import botocore.session
from botocore.exceptions import ClientError

__version__ = '1.2.0'

WhoamiInfo = namedtuple('WhoamiInfo', [
    'Account',
    'AccountAliases',
    'Arn',
    'Type',
    'Name',
    'RoleSessionName',
    'UserId',
    'Region',
    'SSOPermissionSet',
])

DESCRIPTION = """\
Show what AWS account and identity you're using.
Formats the output of sts.GetCallerIdentity nicely,
and also gets your account alias (if you're allowed)
"""

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('--profile', help="AWS profile to use")

    parser.add_argument('--json', action='store_true', help="Output as JSON")

    parser.add_argument('--version', action='store_true')

    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    if args.version:
        print(__version__)
        parser.exit()

    try:
        session = botocore.session.Session(profile=args.profile)

        disable_account_alias = os.environ.get('AWS_WHOAMI_DISABLE_ACCOUNT_ALIAS', '')
        if disable_account_alias.lower() in ['', '0', 'false']:
            disable_account_alias = False
        elif disable_account_alias.lower() in ['1', 'true']:
            disable_account_alias = True
        else:
            disable_account_alias = disable_account_alias.split(',')

        whoami_info = whoami(session=session, disable_account_alias=disable_account_alias)

        if args.json:
            print(json.dumps(whoami_info._asdict()))
        else:
            print(format_whoami(whoami_info))
    except Exception as e:
        if args.debug:
            traceback.print_exc()
        err_cls = type(e)
        err_cls_str = err_cls.__name__
        if err_cls.__module__ != 'builtins':
            err_cls_str = '{}.{}'.format(err_cls.__module__, err_cls_str)
        sys.stderr.write('ERROR [{}]: {}\n'.format(err_cls_str, e))
        sys.exit(1)

def format_whoami(whoami_info):
    lines = []
    lines.append(('Account: ', whoami_info.Account))
    for alias in whoami_info.AccountAliases:
        lines.append(('', alias))
    lines.append(('Region: ', whoami_info.Region))
    if whoami_info.SSOPermissionSet:
        lines.append(('AWS SSO: ', whoami_info.SSOPermissionSet))
    else:
        type_str = ''.join(p[0].upper() + p[1:] for p in whoami_info.Type.split('-'))
        lines.append(('{}: '.format(type_str), whoami_info.Name))
    if whoami_info.RoleSessionName:
        lines.append(('RoleSessionName: ', whoami_info.RoleSessionName))
    lines.append(('UserId: ', whoami_info.UserId))
    lines.append(('Arn: ', whoami_info.Arn))
    max_len = max(len(l[0]) for l in lines)
    return '\n'.join("{}{}".format(l[0].ljust(max_len), l[1]) for l in lines)

def whoami(session=None, disable_account_alias=False):
    """Return a WhoamiInfo namedtuple.

    Args:
        session: An optional boto3 or botocore Session
        disable_account_alias (bool): Disable checking the account alias

    Returns:
        WhoamiInfo: Data on the current IAM principal, account, and region.

    """
    if session is None:
        session = botocore.session.get_session()
    elif hasattr(session, '_session'): # allow boto3 Session as well
        session = session._session

    data = {}
    data['Region'] = session.get_config_variable('region')

    response = session.create_client('sts').get_caller_identity()

    for field in ['Account', 'Arn', 'UserId']:
        data[field] = response[field]

    data['Type'], name = data['Arn'].rsplit(':', 1)[1].split('/',1)

    if data['Type'] == 'assumed-role':
        data['Name'], data['RoleSessionName'] = name.rsplit('/', 1)
    else:
        data['Name'] = name
        data['RoleSessionName'] = None

    if data['Type'] == 'assumed-role' and data['Name'].startswith('AWSReservedSSO'):
        try:
            # format is AWSReservedSSO_{permission-set}_{random-tag}
            data['SSOPermissionSet'] = data['Name'].split('_', 1)[1].rsplit('_', 1)[0]
        except Exception as e:
            data['SSOPermissionSet'] = None
    else:
        data['SSOPermissionSet'] = None

    data['AccountAliases'] = []
    if not isinstance(disable_account_alias, bool):
        for value in disable_account_alias:
            if data['Account'].startswith(value) or data['Account'].endswith(value):
                disable_account_alias = True
                break
            fields = ['Name', 'Arn', 'RoleSessionName']
            if any(value == data[field] for field in fields):
                disable_account_alias = True
                break
    if not disable_account_alias:
        try:
            #pedantry
            paginator = session.create_client('iam').get_paginator('list_account_aliases')
            for response in paginator.paginate():
                data['AccountAliases'].extend(response['AccountAliases'])
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') != 'AccessDenied':
                raise

    return WhoamiInfo(**data)

if __name__ == '__main__':
    main()
