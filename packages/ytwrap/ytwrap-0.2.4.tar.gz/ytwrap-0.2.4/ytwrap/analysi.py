import json
import time
from datetime import datetime
from typing import Optional, Callable

class YTAnalysis:
    def __init__(self, channel_id: str, json_path: str):
        self.channel_id = channel_id
        self.json_path = json_path
        self._fetched = False

    def fetch_current_subscribers(self, fetch_func: Callable[[str], int]) -> int:
        count = fetch_func(self.channel_id)
        self._fetched = True
        self.record_subscriber_growth(count)
        return count

    def record_subscriber_growth(self, count: int, date: Optional[datetime] = None, subscribe_client=None):
        if not self._fetched:
            raise RuntimeError("fetch_current_subscribersを先に実行してください")
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")  # 時刻も保存

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        if data:
            last = data[-1]
            last_count = last["subscribers"]
            last_date = datetime.strptime(last["date"], "%Y-%m-%d %H:%M:%S")
            seconds = (date - last_date).total_seconds()
            hours = seconds / 3600 if seconds else 1
            growth = (count - last_count) / hours
        else:
            growth = 0

        data.append({
            "channel_id": self.channel_id,
            "date": date_str,
            "subscribers": count,
            "growth_per_hour": growth
        })

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if subscribe_client is not None and hasattr(subscribe_client, "add_history"):
            subscribe_client.add_history(count, date)

    def start_monitoring(
        self,
        fetch_func: Callable[[str], int],
        interval_seconds: int = 3600,
        subscribe_client=None,
        stop_after: Optional[int] = None
    ):
        """
        指定間隔ごとに自動で登録者数を監視・記録する
        :param fetch_func: 登録者数取得関数
        :param interval_seconds: 監視間隔（秒）
        :param subscribe_client: YTSubscribeClient（任意）
        :param stop_after: 監視ループ回数（Noneなら無限）
        """
        self.fetch_current_subscribers(fetch_func)
        count = 0
        while stop_after is None or count < stop_after:
            time.sleep(interval_seconds)
            subs = fetch_func(self.channel_id)
            self.record_subscriber_growth(subs, subscribe_client=subscribe_client)
            count += 1
            print(f"[{datetime.now()}] 登録者数: {subs} を記録しました")

# 使い方例（1時間ごと、無制限ループ）
# ana = YTAnalysis("UCxxxx", "growth.json")
# ana.start_monitoring(fetch_current_subscribers, interval_seconds=3600)