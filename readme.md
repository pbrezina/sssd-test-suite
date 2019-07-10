# Virtual Test Suite for SSSD

Virtual Test Suite for SSSD is a set of Vagrant and Ansible scripts that
will automatically setup and provision several virtual machines that you
can use to test SSSD.

It creates an out of the box working virtual environment with 389 Directory
Server, IPA and Active Directory servers. It also creates an SSSD client
machine enrolled to those servers, ready to build and debug your code.

## Table Of Contents

1. [Basic usage](./docs/basic-usage.md)
2. [Guest description](./docs/guests.md)
3. [Configuration file](./docs/configuration.md)
4. [Environment variables](./docs/environment-variables.md)
5. [Tips and Tricks](./docs/tips.md)
6. [Running SSSD tests](./docs/running-tests.md)
7. [Creating new boxes](./docs/new-boxes.md)

