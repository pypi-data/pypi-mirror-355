from datetime import datetime
import os
import json

import ytwrap  # ← ここだけでOK

TEST_JSON = "test_growth_history.json"
if os.path.exists(TEST_JSON):
    os.remove(TEST_JSON)

CHANNEL_ID = "UC_TESTCHANNELID"
test_data = [
    (datetime(2025, 6, 10), 8000),
    (datetime(2025, 6, 11), 8500),
    (datetime(2025, 6, 12), 9000),
]

ana = ytwrap.YTAnalysis(CHANNEL_ID, TEST_JSON)
sub_client = ytwrap.YTSubscribeClient(CHANNEL_ID)

for dt, cnt in test_data:
    ana.record_subscriber_growth(cnt, date=dt, subscribe_client=sub_client)

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