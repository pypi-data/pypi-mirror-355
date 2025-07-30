<!--
Copyright (C) 2024 Maxwell G <maxwell@gtmx.me>
SPDX-License-Identifier: MIT
-->

# Contributing

This project's mailing list is
[~gotmax23/zstarfile@lists.sr.ht][mailto] ([archives]).

Development, issue reporting, and project discussion happen on the mailing
list.

## Issue Reporting and Feature Requests

Direct these to the mailing list. zstarfile has a [ticket tracker][tracker] on
todo.sr.ht, but it's only for confirmed issues.

## Patches

Contributions are always welcome!
It is recommended that you send a message to the mailing list before working on
a larger change.

Patches can be sent to [~gotmax23/zstarfile@lists.sr.ht][mailto]
using [`git send-email`][1].
No Sourcehut account is required!

After configuring git-send-email as explained at [git-send-email.io][1]:

``` bash
git clone https://git.sr.ht/~gotmax23/zstarfile
cd zstarfile

# First time only
git config sendemail.to "~gotmax23/zstarfile@lists.sr.ht"
git config format.subjectprefix "PATCH zstarfile"

$EDITOR ...

nox

git commit -a -v
git send-email origin/main
```

See [git-send-email.io][1] for more details.

If you prefer, git.sr.ht has a webui to help you submit patches to a mailing
list that can be used in place of `git send-email`. You can follow [this
written guide][2] or [this video guide][3] for how to use the webui.

[mailto]: mailto:~gotmax23/gtmx.me@lists.sr.ht
[archives]: https://lists.sr.ht/~gotmax23/gtmx.me
[tracker]: https://todo.sr.ht/~gotmax23/gtmx.me
[1]: https://git-send-email.io
[2]: https://man.sr.ht/git.sr.ht/#sending-patches-upstream
[3]: https://spacepub.space/w/no6jnhHeUrt2E5ST168tRL
