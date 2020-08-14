# aws-whoami
**Show what AWS account and identity you're using**

You should know about [`aws sts get-caller-identity`](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html),
which sensibly returns the identity of the caller. But even with `--output table`, I find this a bit lacking.
That ARN is a lot to visually parse, it doesn't tell you what region you're configured to use, and I am not very good at remembering AWS account numbers.
`aws-whoami` makes it better.

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
your account alias won't appear.

## Install

I recommend you install `aws-whoami` with [`pipx`](https://pipxproject.github.io/pipx/), which installs the tool in an isolated virtualenv while linking the script you need.

```bash
# with pipx
pipx install aws-whoami

# without pipx
python -m pip install --user aws-whoami
```

## Options

`aws-whoami` uses [`boto3`](boto3.amazonaws.com/v1/documentation/api/latest/index.html), so it'll pick up your credentials in [the normal ways](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#config-settings-and-precedence),
including with the `--profile` parameter.

If you'd like the output as a JSON object, that's the `--json` flag.

## Other uses
If you don't want to install it, the `aws_whoami.py` file can be used on its own, with only a dependency on `boto3`.

If you want to use it as a library, the `whoami()` function, which optionally takes a `boto3.Session`, returns a `WhoamiInfo` namedtuple.
