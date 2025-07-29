import re
import sys
import subprocess
import shutil
import os

SETUP_PATH = "setup.py"

# バージョン番号を種別ごとに上げる
# kind: 'patch', 'minor', 'major'
def bump_version(version: str, kind: str) -> str:
    parts = [int(p) for p in version.strip().split(".")]
    if kind == "patch":
        parts[2] += 1
    elif kind == "minor":
        parts[1] += 1
        parts[2] = 0
    elif kind == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    else:
        raise ValueError("kindはpatch, minor, majorのいずれか")
    return f"{parts[0]}.{parts[1]}.{parts[2]}"

def main():
    print("バージョンアップの種類を選択してください:")
    print("1: patch (例: 0.1.0 → 0.1.1)")
    print("2: minor (例: 0.1.0 → 0.2.0)")
    print("3: major (例: 0.1.0 → 1.0.0)")
    kind_map = {"1": "patch", "2": "minor", "3": "major"}
    kind = input("番号を入力: ").strip()
    if kind not in kind_map:
        print("無効な選択です")
        sys.exit(1)
    kind = kind_map[kind]

    with open(SETUP_PATH, encoding="utf-8") as f:
        setup_code = f.read()

    m = re.search(r'version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', setup_code)
    if not m:
        print("setup.py からバージョン番号を検出できませんでした")
        sys.exit(1)
    old_version = m.group(1)
    new_version = bump_version(old_version, kind)

    new_code = re.sub(
        r'(version\s*=\s*["\'])[0-9]+\.[0-9]+\.[0-9]+(["\'])',
        r'\g<1>' + new_version + r'\2',
        setup_code
    )

    with open(SETUP_PATH, "w", encoding="utf-8") as f:
        f.write(new_code)

    print(f"バージョンを {old_version} → {new_version} に更新しました")

    # dist, build, egg-infoを削除
    for folder in ["dist", "build", "ytwrap.egg-info"]:
        if os.path.exists(folder):
            print(f"{folder} を削除します...")
            shutil.rmtree(folder)

    # パッケージビルド
    print("パッケージをビルド中...")
    subprocess.run([sys.executable, "setup.py", "sdist", "bdist_wheel"], check=True)

    # PyPIにアップロード
    print("PyPIにアップロードします...")
    subprocess.run(["twine", "upload", "dist/*"])

if __name__ == "__main__":
    main()
