from datetime import datetime
import os
import json
import ytwrap  # ← ここだけでOK

# --- 設定 ---
TEST_JSON = "test_growth_history.json"
CHANNEL_ID = "UCYrHEsf7bhiFJssY5btS7Zg"

# テスト用登録者データ（サンプル）
test_data = [
    (datetime(2025, 6, 10), 2000),
    (datetime(2025, 6, 11), 2500),
    (datetime(2025, 6, 12), 3000),
]

# テスト用ファイルがあれば削除
if os.path.exists(TEST_JSON):
    os.remove(TEST_JSON)

# --- YouTube登録者数取得関数（APIキーは環境変数でセット済みを想定） ---
import os
import requests

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

# --- 初期化 ---
ana = ytwrap.YTAnalysis(CHANNEL_ID, TEST_JSON)

# record_subscriber_growthを使う前にfetch_current_subscribersを呼ぶ（初回のみ必須）
# 本番用: 下の行のコメントを外してください
# ana.fetch_current_subscribers(fetch_youtube_subscribers)

# テスト用: サンプルデータ（1日目）をダミー関数で登録
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