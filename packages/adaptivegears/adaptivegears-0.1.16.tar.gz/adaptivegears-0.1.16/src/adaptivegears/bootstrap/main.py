import collections
import os
import re
import sys
import requests
import tarfile
import tempfile

from . import workspace

Ansible = collections.namedtuple('Ansible', ['collection', 'playbook', 'variables'])

REGEX_KEY = re.compile(r'^--?([a-zA-Z0-9_\-]+)=?')
USERDIR = os.environ['USER_PWD']

def parse_arguments(argv):
    r = {}

    key = None
    while argv:
        arg = argv.pop(0)

        m = REGEX_KEY.match(arg)
        if m:
            if key:
                r[key] = True
            key = m.group(1)

            arg = arg.replace(m.group(0), "")
            if arg:
                argv.insert(0, arg)
        else:
            if key:
                r[key] = arg
                key = None
                continue
            else:
                # noop: value without key
                pass

    if key:
        r[key] = True

    out = {}
    for k, v in r.items():
        k = k.replace('-', '_')

        if isinstance(v, str) and v.isdigit():
            v = int(v)
        elif v == 'true':
            v = True
        elif v == 'false':
            v = False
        out[k] = v

    return out


def parse(tempdir):
    if len(sys.argv) == 1:
        print('Usage: bootstrap <collection> <playbook> [extra_vars]')
        sys.exit(1)
    argv = sys.argv[1:]

    collection = argv[0]

    if collection.startswith('@'):
        # @owner/playbook/reference ~ github.com/<owner>/ansible-collection-actions//playbooks/<playbook>.yml
        # @andreygubarev/ping/v1.0.0
        organization, playbook = collection.split('/', 1)
        if '/' in playbook:
            playbook, reference = playbook.split('/', 1)
        else:
            reference = 'main'
        organization = organization[1:]

        github_url = f'https://codeload.github.com/{organization}/ansible-collection-actions/tar.gz/{reference}'
        r = requests.get(github_url)
        r.raise_for_status()
        with open(os.path.join(tempdir, 'collection.tar.gz'), 'wb') as f:
            f.write(r.content)

        collection = os.path.join(tempdir, 'collection')
        with tarfile.open(os.path.join(tempdir, 'collection.tar.gz')) as tar:
            tar.extractall(collection)

        # If collection folder has exactly one dir, use it as collection root
        subdirs = [d for d in os.listdir(collection) if os.path.isdir(os.path.join(collection, d))]
        if len(subdirs) == 1:
            collection = os.path.join(collection, subdirs[0])

        playbook = os.path.join(collection, 'playbooks', f'{playbook}.yml')
        argv.insert(1, playbook)

    if len(argv) < 2:
        print('Usage: bootstrap <collection> <playbook> [extra_vars]')
        sys.exit(1)

    if not os.path.isabs(collection):
        collection = os.path.join(USERDIR, collection)
    if not (os.path.exists(collection) and os.path.isdir(collection)):
        raise FileNotFoundError(f'Collection not found: {collection}')
    if not os.access(collection, os.R_OK):
        raise PermissionError(f'Collection is not readable: {collection}')

    playbook = argv[1]
    if not os.path.isabs(playbook):
        playbook = os.path.join(USERDIR, playbook)
    if not (os.path.exists(playbook) and os.path.isfile(playbook)):
        raise FileNotFoundError(f'Playbook not found: {playbook}')
    if not os.access(playbook, os.R_OK):
        raise PermissionError(f'Playbook is not readable: {playbook}')

    variables = parse_arguments(argv[2:])
    return Ansible(collection, playbook, variables)


def main():
    with tempfile.TemporaryDirectory(prefix='bootstrap-tmp-') as tempdir:
        ansible = parse(tempdir=tempdir)
        with tempfile.TemporaryDirectory(prefix='bootstrap-') as workdir:
            ws = workspace.Workspace(workdir, ansible)
            workspace.clone(ws)
            workspace.execute(ws)

if __name__ == '__main__':
    main()
