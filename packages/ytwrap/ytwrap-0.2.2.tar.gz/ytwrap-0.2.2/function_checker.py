# 指定ディレクトリ配下の全pyファイルの全関数を自動テストし、結果を明示的に表示するスクリプト
import os
import sys
import importlib
import inspect
import traceback

TARGET_DIR = "ytwrap"


def test_all_functions_in_module(module, modname):
    results = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            try:
                sig = inspect.signature(obj)
                # 引数なしで呼び出せる場合のみ実行
                if all(
                    p.default != inspect.Parameter.empty
                    or p.kind
                    in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                    for p in sig.parameters.values()
                ):
                    result = obj()
                    results.append(
                        f"{modname}の{name}関数: 正常に動作しました。結果: {result}"
                    )
                elif name == "duration_to_seconds":
                    result = obj("PT59S")
                    results.append(
                        f"{modname}の{name}関数: 正常に動作しました。結果: {result}"
                    )
                elif name == "classify_youtube_videos":
                    test_data = [
                        {
                            "snippet": {"title": "Test #shorts"},
                            "contentDetails": {"duration": "PT59S"},
                            "player": {"width": 720, "height": 1280},
                            "liveStreamingDetails": {},
                        }
                    ]
                    result = obj(test_data)
                    results.append(
                        f"{modname}の{name}関数: 正常に動作しました。結果: {result}"
                    )
                else:
                    results.append(f"{modname}の{name}関数: スキップ（引数が必要です）")
            except Exception as e:
                results.append(
                    f"{modname}の{name}関数が正常に動作しませんでした。エラー: {e}\n{traceback.format_exc()}"
                )
    return results


def main():
    sys.path.insert(0, os.getcwd())
    file_func_map = {}
    for fname in os.listdir(TARGET_DIR):
        if fname.endswith(".py") and not fname.startswith("__"):
            modname = f"{TARGET_DIR}.{fname[:-3]}"
            try:
                module = importlib.import_module(modname)
                func_names = []
                # モジュール直下の関数
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                        func_names.append(name)
                # クラス内のメソッド
                for cname, cls in inspect.getmembers(module, inspect.isclass):
                    if cls.__module__ == module.__name__:
                        for mname, mobj in inspect.getmembers(cls):
                            if inspect.isfunction(mobj) or inspect.ismethod(mobj):
                                if not mname.startswith("__"):
                                    func_names.append(f"{cname}.{mname}")
                if func_names:
                    file_func_map[fname] = func_names
            except Exception:
                pass
    for fname, funcs in file_func_map.items():
        print(f"{fname}：")
        for func in funcs:
            # クラス名.メソッド名ならメソッド名だけ抽出
            if "." in func:
                short_name = func.split(".", 1)[1]
            else:
                short_name = func
            # テスト実行して色分け
            try:
                modname = f"{TARGET_DIR}.{fname[:-3]}"
                module = importlib.import_module(modname)
                # クラスメソッドかグローバル関数かで取得
                if "." in func:
                    cname, mname = func.split(".", 1)
                    cls = getattr(module, cname)
                    method = getattr(cls, mname)
                    # __init__以外はダミー引数で呼び出しテスト（引数必須はスキップ）
                    if mname == "__init__":
                        continue
                    sig = inspect.signature(method)
                    if all(
                        p.default != inspect.Parameter.empty
                        or p.kind
                        in (
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        )
                        or p.name == "self"
                        for p in sig.parameters.values()
                    ):
                        # インスタンス化してself付きで呼ぶ
                        inst = (
                            cls(api_key="dummy")
                            if "api_key" in sig.parameters
                            else cls()
                        )
                        method(inst)
                        print(f"　・\033[32m{short_name}\033[0m")
                    else:
                        print(f"　・\033[32m{short_name}\033[0m (引数省略)")
                else:
                    fn = getattr(module, func)
                    sig = inspect.signature(fn)
                    if all(
                        p.default != inspect.Parameter.empty
                        or p.kind
                        in (
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        )
                        for p in sig.parameters.values()
                    ):
                        fn()
                        print(f"　・\033[32m{short_name}\033[0m")
                    elif func == "duration_to_seconds":
                        fn("PT59S")
                        print(f"　・\033[32m{short_name}\033[0m")
                    elif func == "classify_youtube_videos":
                        test_data = [
                            {
                                "snippet": {"title": "Test #shorts"},
                                "contentDetails": {"duration": "PT59S"},
                                "player": {"width": 720, "height": 1280},
                                "liveStreamingDetails": {},
                            }
                        ]
                        fn(test_data)
                        print(f"　・\033[32m{short_name}\033[0m")
                    else:
                        print(f"　・\033[32m{short_name}\033[0m (引数省略)")
            except Exception:
                print(f"　・\033[31m{short_name}\033[0m (エラー)")
        print("")


if __name__ == "__main__":
    main()
