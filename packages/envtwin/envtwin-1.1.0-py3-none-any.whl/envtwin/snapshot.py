import platform
import subprocess
import json
import os

def get_os_info():
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),}
def get_env_vars():
    blacklist = {'PWD', 'OLDPWD', 'LS_COLORS', 'SSH_AUTH_SOCK', 'XDG_SESSION_ID', 'XDG_RUNTIME_DIR', 'HOME', 'USER', 'PATH', 'SHELL'}
    return {k: v for k, v in os.environ.items() if k not in blacklist}
def get_shell_configs():
    home = os.path.expanduser('~')
    configs = {}
    for fname in ['.bashrc', '.zshrc', '.profile', '.bash_profile']:
        path = os.path.join(home, fname)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    configs[fname] = f.read()
            except Exception:
                configs[fname] = '<unreadable>'
    return configs
def get_npm_packages():
    try:
        npm = subprocess.getoutput('npm list -g --depth=0 --json')
        return json.loads(npm).get('dependencies', {})
    except Exception:
        return {}
def get_installed_packages():
    pip = subprocess.getoutput('pip freeze')
    try:
        apt = subprocess.getoutput('apt-mark showmanual')
    except Exception:
        apt = ''
    return {
        'pip': pip.splitlines(),
        'apt': apt.splitlines(),
        'npm': get_npm_packages(),
    }
def get_editors():
    editors = []
    for editor in ['code', 'vim', 'nano', 'emacs', 'subl']:
        if subprocess.getoutput(f'which {editor}'):
            editors.append(editor)
    return editors
def get_databases():
    dbs = []
    for db in ['mysql', 'psql', 'mongod', 'redis-server']:
        if subprocess.getoutput(f'which {db}'):
            dbs.append(db)
    return dbs
def get_open_ports():
    try:
        output = subprocess.getoutput("ss -tuln")
        return output.splitlines()
    except Exception:
        return []
def snapshot_system():
    snapshot = {
        'os': get_os_info(),
        'env_vars': get_env_vars(),
        'shell_configs': get_shell_configs(),
        'packages': get_installed_packages(),
        'editors': get_editors(),
        'databases': get_databases(),
        'ports': get_open_ports(),
    }
    return snapshot
