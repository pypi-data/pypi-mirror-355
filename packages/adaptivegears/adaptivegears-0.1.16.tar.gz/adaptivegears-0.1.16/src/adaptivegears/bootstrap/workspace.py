import collections
import json
import os
import shutil
import sys

import ansible_runner


Workspace = collections.namedtuple('Workspace', ['workdir', 'ansible'])

WORKSPACE_INVENTORY = lambda w: os.path.join(w.workdir, 'inventory')
WORKSPACE_HOSTS = lambda w: os.path.join(w.workdir, 'inventory', 'hosts')
WORKSPACE_HOSTVARS = lambda w: os.path.join(w.workdir, 'inventory', 'host_vars')
WORKSPACE_LOCALHOST = lambda w: os.path.join(w.workdir, 'inventory', 'host_vars', 'localhost.yml')

WORKSPACE_PROJECT = lambda w: os.path.join(w.workdir, 'project')
WORKSPACE_PLAYBOOK = lambda w, pb: os.path.join(w.workdir, 'project', pb)
WORKSPACE_ROLES = lambda w: os.path.join(w.workdir, 'project', 'roles')
WORKSPACE_PLUGINS = lambda w: os.path.join(w.workdir, 'project', 'plugins')

WORKSPACE_REQUIREMENTS = lambda w: os.path.join(w.workdir, 'requirements.yml')

WORKSPACE_ARTIFACTS = lambda w: os.path.join(w.workdir, 'artifacts')
WORKSPACE_ENVIRONMENT = lambda w: os.path.join(w.workdir, 'env')

ANSIBLE_CONFIG = '''
[defaults]
callbacks_enabled = community.general.opentelemetry
[callback_opentelemetry]
enable_from_environment = ANSIBLE_OPENTELEMETRY_ENABLED
'''

def clone(ws):
    # requirements
    requirements = None
    for r in ['requirements.yml', 'requirements.yaml']:
        if os.path.exists(os.path.join(ws.ansible.collection, r)):
            requirements = os.path.join(ws.ansible.collection, r)
            break
    if requirements:
        shutil.copy2(requirements, WORKSPACE_REQUIREMENTS(ws))

    # inventory
    os.makedirs(WORKSPACE_INVENTORY(ws))
    with open(WORKSPACE_HOSTS(ws), 'w') as f:
        f.write('localhost')
    os.makedirs(WORKSPACE_HOSTVARS(ws))
    with open(WORKSPACE_LOCALHOST(ws), 'w') as f:
        f.write('---\n')
        f.write('ansible_connection: local\n')
        f.write(f'ansible_python_interpreter: {sys.executable}')

    # project
    os.makedirs(WORKSPACE_PROJECT(ws))
    playbook = os.path.basename(ws.ansible.playbook)
    shutil.copy2(ws.ansible.playbook, WORKSPACE_PLAYBOOK(ws, playbook))

    roles = os.path.join(ws.ansible.collection, 'roles')
    if os.path.exists(roles):
        shutil.copytree(roles, WORKSPACE_ROLES(ws))

    plugins = os.path.join(ws.ansible.collection, 'plugins')
    if os.path.exists(plugins):
        shutil.copytree(plugins, WORKSPACE_PLUGINS(ws))

    # artifacts
    os.makedirs(WORKSPACE_ARTIFACTS(ws))

    # config
    with open(os.path.join(ws.workdir, 'ansible.cfg'), 'w') as f:
        f.write(ANSIBLE_CONFIG)

    # environment
    os.makedirs(WORKSPACE_ENVIRONMENT(ws))
    envvars = dict(os.environ)
    envvars['ANSIBLE_CONFIG'] = os.path.join(ws.workdir, 'ansible.cfg')
    with open(os.path.join(WORKSPACE_ENVIRONMENT(ws), 'envvars'), 'w') as f:
        json.dump(envvars, f)


def execute(ws):
    if os.path.exists(os.path.join(ws.workdir, 'requirements.yml')):
        stdout, stderr, rc = ansible_runner.run_command(
            host_cwd=ws.workdir,
            private_data_dir=ws.workdir,
            executable_cmd='ansible-galaxy',
            cmdline_args=['collection', 'install', '-r', 'requirements.yml'],
            input_fd=sys.stdin,
            output_fd=sys.stdout,
            error_fd=sys.stderr,
            envvars=os.environ,
            rotate_artifacts=0,
        )
        if rc != 0:
            raise RuntimeError('Failed to install collection dependencies')

    playbook = os.path.basename(ws.ansible.playbook)
    ansible_runner.run(
        private_data_dir=ws.workdir,
        playbook=playbook,
        extravars=ws.ansible.variables,
        limit='localhost',
        rotate_artifacts=0,
        quiet=False,
    )
    return 0
