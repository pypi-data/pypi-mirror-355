import argparse
import os
import subprocess
import socket
import sys

SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")

def parse_ssh_config(path):
    hosts = []
    current = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, *value = line.split()
            value = ' '.join(value)
            if key.lower() == 'host':
                if current:
                    hosts.append(current)
                    current = {}
                current['Host'] = value
            else:
                current[key] = value
        if current:
            hosts.append(current)
    return hosts

def fuzzy_match(hosts, query, exact=False):
    if exact:
        return [h for h in hosts if query == h['Host']]
    q = query.lower()
    return [h for h in hosts if q in h['Host'].lower()]

def is_reachable(hostname, port, timeout=2.0):
    try:
        with socket.create_connection((hostname, port), timeout):
            return True
    except Exception:
        return False

def connect_via_ssh(alias):
    subprocess.run(["ssh", alias])

def main():
    parser = argparse.ArgumentParser(description="Smart SSH connector")
    parser.add_argument("query", help="Fuzzy or exact SSH host name")
    parser.add_argument("--pick", action="store_true", help="Pick manually from matches")
    parser.add_argument("--list", action="store_true", help="List all matched hosts and reachable status")
    parser.add_argument("--dry-run", action="store_true", help="Show which host would be connected to without connecting")
    parser.add_argument("--exact", action="store_true", help="Use exact host match instead of fuzzy")
    args = parser.parse_args()

    if not os.path.exists(SSH_CONFIG_PATH):
        print(f"❌ SSH config file not found: {SSH_CONFIG_PATH}")
        return

    hosts = parse_ssh_config(SSH_CONFIG_PATH)
    matched = fuzzy_match(hosts, args.query, exact=args.exact)

    if not matched:
        print(f"❌ No match found for '{args.query}'")
        return

    print(f"🔍 Matching: {args.query} → {[h['Host'] for h in matched]}")

    reachable = []
    for h in matched:
        hostname = h.get('HostName')
        port = int(h.get('Port', 22))
        if is_reachable(hostname, port):
            reachable.append(h)

    if args.list:
        for idx, h in enumerate(matched):
            hostname = h.get('HostName')
            port = int(h.get('Port', 22))
            status = "✅" if is_reachable(hostname, port) else "❌"
            print(f"{idx}. {status} {h['Host']} ({hostname}:{port})")
        return

    if args.pick:
        for idx, h in enumerate(matched):
            hostname = h.get('HostName')
            port = int(h.get('Port', 22))
            status = "✅" if is_reachable(hostname, port) else "❌"
            print(f"{idx}. {status} {h['Host']} ({hostname}:{port})")
        try:
            choice = int(input("\nChoose a number to connect: "))
            selected = matched[choice]
            if is_reachable(selected.get('HostName'), int(selected.get('Port', 22))):
                print(f"🚀 Connecting to {selected['Host']}...")
                if not args.dry_run:
                    connect_via_ssh(selected['Host'])
            else:
                print("❌ Selected host is not reachable.")
        except KeyboardInterrupt:
            print("\n❌ Interrupted. Exiting.")
        except Exception as e:
            print(f"❌ Invalid choice: {e}")
        return

    if not reachable:
        print("❌ No reachable hosts found.")
        return

    first = reachable[0]
    print(f"✅ Reachable: {first['Host']} ({first.get('HostName')}:{first.get('Port', 22)})")
    if args.dry_run:
        print(f"🔁 Would connect to {first['Host']} (dry run)")
    else:
        print(f"🚀 Connecting to {first['Host']}...")
        connect_via_ssh(first['Host'])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrupted. Exiting.")
        sys.exit(1)