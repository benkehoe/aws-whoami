# aws-whoami
**Show what AWS account and identity you're using**

You should know about [`aws sts get-caller-identity`](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html),
which sensibly returns the identity of the caller. But even with `--output table`, I find this a bit lacking.
That ARN is a lot to visually parse, it doesn't tell you what region your credentials are configured for,
and I am not very good at remembering AWS account numbers. `aws-whoami` makes it better.

```
$ aws-whoami
Account:         123456789012
                 my-account-alias
Region:          us-east-2
AssumedRole:     MY-ROLE
RoleSessionName: ben
UserId:          SOMEOPAQUEID:ben
Arn:             arn:aws:sts::123456789012:assumed-role/MY-ROLE/ben
```

Note: if you don't have permissions to [iam:ListAccountAliases](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAccountAliases.html),
your account alias won't appear. See below for disabling this check if getting a permission denied on this call raises flags in your organization.

## Install

I recommend you install `aws-whoami` with [`pipx`](https://pipxproject.github.io/pipx/), which installs the tool in an isolated virtualenv while linking the script you need.

```bash
# with pipx
pipx install aws-whoami

# without pipx
python -m pip install --user aws-whoami
```

If you don't want to install it, the [`aws_whoami.py`](https://raw.githubusercontent.com/benkehoe/aws-whoami/master/aws_whoami.py) file can be used on its own, with only a dependency on `botocore` (which comes with `boto3`).

## Options

`aws-whoami` uses [`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html), so it'll pick up your credentials in [the normal ways](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#config-settings-and-precedence),
including with the `--profile` parameter.

If you'd like the output as a JSON object, that's the `--json` flag.
The output is the `WhoamiInfo` object (see below) as a JSON object.

To full disable account alias checking, set the environment variable `AWS_WHOAMI_DISABLE_ACCOUNT_ALIAS` to `true`.
To selectively disable it, you can also set it to a comma-separated list of values that will be matched against the following:
* The beginning or end of the account number
* The principal Name or ARN
* The role session name

## As a library

The library has a `whoami()` function, which optionally takes a `Session` (either `boto3` or `botocore`), and returns a `WhoamiInfo` namedtuple.

The fields of `WhoamiInfo` are:
* `Account`
* `AccountAliases` (NOTE: this is a list)
* `Arn`
* `Type`
* `Name`
* `RoleSessionName`
* `UserId`
* `Region`
* `SSOPermissionSet`

`Type`, `Name`, and `RoleSessionName` (and `SSOPermissionSet`) are split from the ARN for convenience.
`RoleSessionName` is `None` for IAM users.

`SSOPermissionSet` is set if the assumed role name conforms to the format `AWSReservedSSO_{permission-set}_{random-tag}`.

To disable the account alias check, pass `disable_account_alias=True` to `whoami()`.
Note that the `AccountAliases` field will then be an empty list, not `None`.

`format_whoami()` takes a `WhoamiInfo` object and returns the formatted string used for display.
