# EnvTwin
# Still In Active Development
# Its a Beta Version

EnvTwin is an instant environment re-creator. It snapshots your system setup (OS, packages, editors, databases, ports, etc.), converts it into a Dockerfile or setup script, and lets you share it with one click—like a dev VM twin for onboarding.

## Features
- Snapshots OS, installed packages (pip, apt, npm), editors, databases, open ports
- Captures environment variables and shell config files
- Generates a Dockerfile to reproduce your environment
- Exports snapshot to a JSON file

## Usage

Install locally for development:

```sh
pip install -e .
```

Run the CLI:

```sh
envtwin --dockerfile
# or
python -m envtwin --export snapshot.json
```

## License
MIT
