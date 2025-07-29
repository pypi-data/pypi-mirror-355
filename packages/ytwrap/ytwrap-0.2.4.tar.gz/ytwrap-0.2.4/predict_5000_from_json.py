from datetime import datetime
import os
import json
import time
import requests
import ytwrap  # ← ここだけでOK

# --- 設定 ---
TEST_JSON = "test_growth_history.json"
CHANNEL_ID = "UCYrHEsf7bhiFJssY5btS7Zg"

# テスト用登録者データ（サンプル）
test_data = [
    (datetime(2025, 6, 14), 2000),
    (datetime(2025, 6, 15), 2500),
    (datetime(2025, 6, 16), 3000),
]

# テスト用ファイルがあれば削除
if os.path.exists(TEST_JSON):
    os.remove(TEST_JSON)

# --- YouTube登録者数取得関数（APIキーは環境変数でセット済みを想定） ---
def fetch_youtube_subscribers(channel_id: str) -> int:
    api_key = os.environ["YOUTUBE_API_KEY"]  # 例: 環境変数名を合わせてください
    url = (
        "https://www.googleapis.com/youtube/v3/channels"
        f"?part=statistics&id={channel_id}&key={api_key}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return int(data["items"][0]["statistics"]["subscriberCount"])

# --- YTAnalysis拡張: リアルタイム監視機能 ---
def start_monitoring(
    ana, fetch_func, interval_seconds=3600, subscribe_client=None, stop_after=None
):
    """
    指定間隔ごとに自動で登録者数を監視・記録する
    :param ana: YTAnalysisインスタンス
    :param fetch_func: 登録者数取得関数
    :param interval_seconds: 監視間隔（秒）
    :param subscribe_client: YTSubscribeClient（任意）
    :param stop_after: 監視ループ回数（Noneなら無限）
    """
    ana.fetch_current_subscribers(fetch_func)
    count = 0
    while stop_after is None or count < stop_after:
        time.sleep(interval_seconds)
        subs = fetch_func(ana.channel_id)
        ana.record_subscriber_growth(subs, subscribe_client=subscribe_client)
        count += 1
        print(f"[{datetime.now()}] 登録者数: {subs} を記録しました")

# --- 初期化 ---
ana = ytwrap.YTAnalysis(CHANNEL_ID, TEST_JSON)

# record_subscriber_growthを使う前にfetch_current_subscribersを呼ぶ（初回のみ必須、テスト用ダミー）
def dummy_fetch(channel_id):
    return test_data[0][1]
ana.fetch_current_subscribers(dummy_fetch)

sub_client = ytwrap.YTSubscribeClient(CHANNEL_ID)

# 2日目以降のデータを入力
for dt, cnt in test_data[1:]:
    ana.record_subscriber_growth(cnt, date=dt, subscribe_client=sub_client)

# --- 結果表示 ---
print("---- YTSubscribeClient履歴 ----")
for h in sub_client.history:
    print(h)

result = sub_client.predict_milestone_date(10000)
print("\n---- 1万人到達予測 ----")
if result:
    print(f"予想到達日: {result['estimated_date']}（あと{result['days_left']}日）")
    print(f"増加率（1日あたり）: {result['slope']:.2f}")
else:
    print("予測できませんでした")

print("\n---- 保存JSON内容 ----")
with open(TEST_JSON, "r", encoding="utf-8") as f:
    print(json.dumps(json.load(f), ensure_ascii=False, indent=2))

# --- リアルタイム監視の例（1時間ごと、テストでは2回だけ回す） ---
# 実運用時はinterval_seconds=3600（1時間）, stop_after=None（無限ループ）
print("\n---- リアルタイム監視モード ----")
start_monitoring(ana, fetch_youtube_subscribers, interval_seconds=3600, subscribe_client=sub_client, stop_after=2)