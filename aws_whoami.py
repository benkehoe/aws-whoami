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

from __future__ import print_function

import argparse
from collections import namedtuple
import json
import sys
import traceback

import boto3
from botocore.exceptions import ClientError

__version__ = '0.2.2'

WhoamiInfo = namedtuple('WhoamiInfo', [
    'Account',
    'AccountAliases',
    'Arn',
    'Type',
    'Name',
    'RoleSessionName',
    'UserId',
    'Region',
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
        session = boto3.Session(profile_name=args.profile)

        whoami_info = whoami(session)

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
    type_str = ''.join(p[0].upper() + p[1:] for p in whoami_info.Type.split('-'))
    lines.append(('{}: '.format(type_str), whoami_info.Name))
    if whoami_info.RoleSessionName:
        lines.append(('RoleSessionName: ', whoami_info.RoleSessionName))
    lines.append(('UserId: ', whoami_info.UserId))
    lines.append(('Arn: ', whoami_info.Arn))
    max_len = max(len(l[0]) for l in lines)
    return '\n'.join("{}{}".format(l[0].ljust(max_len), l[1]) for l in lines)

def whoami(session=None):
    session = session or boto3.Session()

    data = {}
    data['Region'] = session.region_name

    response = session.client('sts').get_caller_identity()

    for field in ['Account', 'Arn', 'UserId']:
        data[field] = response[field]

    data['Type'], name = data['Arn'].rsplit(':', 1)[1].split('/',1)

    if data['Type'] == 'assumed-role':
        data['Name'], data['RoleSessionName'] = name.rsplit('/', 1)
    else:
        data['Name'] = name
        data['RoleSessionName'] = None

    data['AccountAliases'] = []
    try:
        #pedantry
        paginator = session.client('iam').get_paginator('list_account_aliases')
        for response in paginator.paginate():
            data['AccountAliases'].extend(response['AccountAliases'])
    except ClientError as e:
        if e.response.get('Error', {}).get('Code') != 'AccessDenied':
            raise

    return WhoamiInfo(**data)

if __name__ == '__main__':
    main()
