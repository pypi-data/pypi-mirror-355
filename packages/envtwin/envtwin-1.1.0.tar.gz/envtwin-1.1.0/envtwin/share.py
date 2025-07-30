import json
def export_snapshot(snapshot, filename):
    with open(filename, 'w') as f:
        json.dump(snapshot, f, indent=2)
