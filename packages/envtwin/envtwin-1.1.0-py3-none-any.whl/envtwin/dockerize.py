def generate_dockerfile(snapshot):
    os_info = snapshot['os']
    packages = snapshot['packages']
    editors = snapshot['editors']
    dbs = snapshot['databases']
    base = 'ubuntu:latest' if os_info['system'].lower() == 'linux' else 'debian:latest'
    dockerfile = [f'FROM {base}', 'RUN apt-get update && apt-get install -y \\']
    apt_packages = editors + dbs
    if packages['apt']:
        for line in packages['apt']:
            if '/' in line:
                pkg = line.split('/')[0]
                if pkg not in apt_packages:
                    apt_packages.append(pkg)
    dockerfile.append('    ' + ' \\\n    '.join(apt_packages))
    dockerfile.append('RUN apt-get clean')
    dockerfile.append('RUN apt-get install -y python3-pip')
    if packages['pip']:
        dockerfile.append('RUN pip3 install ' + ' '.join([pkg.split('==')[0] for pkg in packages['pip']]))
    dockerfile.append('CMD ["/bin/bash"]')
    return '\n'.join(dockerfile)
