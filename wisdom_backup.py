"""
wisdom_backup.py v2 — Knowledge Graph Backup
Chay: python wisdom_backup.py
Tu dong tim path Neo4j + Qdrant
"""

import subprocess, json, shutil, time
from datetime import datetime
from pathlib import Path

REPO_DIR   = Path(__file__).parent
BACKUP_DIR = REPO_DIR / "backups"
ERROR_LOG  = REPO_DIR / ".wisdom_errors.json"
TIMESTAMP  = datetime.now().strftime("%Y%m%d_%H%M")

def find_path(patterns):
    for p in patterns:
        path = Path(p).expanduser()
        if path.exists():
            return path
    return None

NEO4J_DATA  = find_path([
    r"C:\Users\LENOVO\.Neo4j\relate-data\dbmss",
    r"C:\Users\LENOVO\AppData\Local\Neo4j\Relate\Data\dbmss",
    r"C:\Neo4j\data",
])
QDRANT_DATA = find_path([
    r"C:\Users\LENOVO\AppData\Local\Qdrant\storage",
    r"C:\Users\LENOVO\.qdrant\storage",
    r"C:\qdrant\storage",
])

def log(status, msg):
    now = datetime.now().isoformat()
    print(f"[{status}] {msg}")
    entry = {"timestamp": now, "source": "backup", "status": status, "message": msg}
    logs = []
    if ERROR_LOG.exists():
        try: logs = json.loads(ERROR_LOG.read_text(encoding="utf-8"))
        except: pass
    ERROR_LOG.write_text(
        json.dumps((logs + [entry])[-500:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def backup_folder(src, name):
    if not src:
        log("WARN", f"{name}: khong tim thay — bo qua. Chay script kiem tra path ben duoi")
        return False
    dest = BACKUP_DIR / name / TIMESTAMP
    dest.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(str(src), str(dest / "data"))
        log("OK", f"{name} -> {dest}")
        return True
    except Exception as e:
        log("ERROR", f"{name} that bai: {e}")
        return False

def backup_git():
    r = subprocess.run(["git", "status", "--porcelain"],
                       capture_output=True, text=True, cwd=REPO_DIR)
    if r.stdout.strip():
        log("WARN", "Git co file chua commit")
    else:
        log("OK", "Git clean")
    return True

def sync_onedrive():
    r = subprocess.run(["rclone", "version"], capture_output=True)
    if r.returncode != 0:
        log("WARN", "rclone chua cai — chi backup local. Tai: https://rclone.org/downloads/")
        return False
    r2 = subprocess.run(
        ["rclone", "sync", str(BACKUP_DIR), "onedrive:/wisdom-backup", "--progress"],
        capture_output=True, text=True
    )
    if r2.returncode == 0:
        log("OK", "OneDrive sync thanh cong")
        return True
    log("ERROR", f"OneDrive sync that bai: {r2.stderr[:200]}")
    return False

def cleanup(keep_days=7):
    cutoff = time.time() - keep_days * 86400
    for item in BACKUP_DIR.rglob("*"):
        if item.is_dir() and item.stat().st_mtime < cutoff:
            try: shutil.rmtree(item)
            except: pass

def main():
    print("=" * 50)
    print(f"wisdom_backup v2 — {TIMESTAMP}")
    print(f"Neo4j  : {NEO4J_DATA or 'KHONG TIM THAY'}")
    print(f"Qdrant : {QDRANT_DATA or 'KHONG TIM THAY'}")
    print("=" * 50)

    results = [
        backup_folder(NEO4J_DATA, "neo4j"),
        backup_folder(QDRANT_DATA, "qdrant"),
        backup_git(),
        sync_onedrive(),
    ]

    ok = sum(results)
    status = "OK" if ok == 4 else "PARTIAL" if ok > 1 else "FAILED"
    log(status, f"Backup {status}: {ok}/4")
    print(f"\nBackup local: {BACKUP_DIR}")

if __name__ == "__main__":
    main()
