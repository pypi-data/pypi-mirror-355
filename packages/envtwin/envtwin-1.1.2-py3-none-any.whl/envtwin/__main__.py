import argparse
from .snapshot import snapshot_system
from .dockerize import generate_dockerfile
from .setupscript import generate_setup_script
from .share import export_snapshot

def main():
    parser = argparse.ArgumentParser(description="EnvTwin: Instant Environment Recreator")
    parser.add_argument('--dockerfile', action='store_true', help='Generate Dockerfile from current environment or if there is no enviroment it will list all packages of the linux OS ur using (Windows not tested yet)')
    parser.add_argument('--setup-script', action='store_true', help='Generate setup script from current environment')
    parser.add_argument('--export', type=str, help='Export snapshot to file')
    args = parser.parse_args()

    snapshot = snapshot_system()
    if args.dockerfile:
        dockerfile = generate_dockerfile(snapshot)
        with open('Dockerfile', 'w') as f:
            f.write(dockerfile)
        print('Dockerfile written to Dockerfile')
    if args.setup_script:
        setup_script = generate_setup_script(snapshot)
        with open('setup.sh', 'w') as f:
            f.write(setup_script)
        print('Setup script written to setup.sh')
    if args.export:
        export_snapshot(snapshot, args.export)

if __name__ == "__main__":
    main()
