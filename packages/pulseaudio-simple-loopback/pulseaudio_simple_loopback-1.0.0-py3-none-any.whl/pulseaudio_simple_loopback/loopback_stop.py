import subprocess
from pathlib import Path

path = Path("/tmp/loopback_modules")

def main():
    result = subprocess.run(["pactl", "list", "short", "modules"], capture_output=True, text=True)
    modules = result.stdout.strip().split('\n')

    loopback_ids = []
    for line in modules:
        parts = line.split('\t')
        if len(parts) >= 2 and "module-loopback" in parts[1]:
            loopback_ids.append(parts[0])

    if not loopback_ids:
        print("No loopback modules found")
        return

    for loopback_id in loopback_ids:
        print(f"Unloading module-loopback ID {loopback_id}...")
        subprocess.run(["pactl", "unload-module", loopback_id], check=True)

    print(f"Unloaded {len(loopback_ids)} loopback modules")

if __name__ == "__main__":
    main()
