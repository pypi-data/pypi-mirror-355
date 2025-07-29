from ytwrap.subscribe import YTSubscribeClient

# 対象チャンネル: UCYrHEsf7bhiFJssY5btS7Zg
history = [
    ("2025-05-01", 3200),
    ("2025-05-10", 3400),
    ("2025-05-20", 3700),
    ("2025-06-01", 4100),
    ("2025-06-10", 4500),
]

# 目標登録者数
TARGET = 5000

client = YTSubscribeClient()
result = client.predict_milestone_date(history, TARGET)

if result:
    print(f"登録者{TARGET}人突破予測日: {result['estimated_date']}")
    print(f"あと{result['days_left']}日 (1日あたり増加数: {result['slope']:.2f})")
else:
    print("予測できませんでした（登録者数が増加していない、または履歴が不足）")
