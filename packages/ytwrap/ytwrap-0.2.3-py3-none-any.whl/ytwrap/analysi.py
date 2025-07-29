import json
from datetime import datetime
from typing import Optional, Callable

class YTAnalysis:
    def __init__(self, channel_id: str, json_path: str):
        """
        :param channel_id: 監視したいYouTubeチャンネルID
        :param json_path: 増加率履歴を保存するJSONファイルのパス
        """
        self.channel_id = channel_id
        self.json_path = json_path
        self._fetched = False  # 初回fetch済みフラグ

    def fetch_current_subscribers(self, fetch_func: Callable[[str], int]) -> int:
        """
        fetch_funcを利用して現在の登録者数を取得し、jsonに保存する
        :param fetch_func: チャンネルIDを受け取って登録者数を返す関数
        :return: 取得した登録者数
        """
        count = fetch_func(self.channel_id)
        self._fetched = True
        self.record_subscriber_growth(count)
        return count

    def record_subscriber_growth(self, count: int, date: Optional[datetime] = None, subscribe_client=None):
        """
        現在の登録者数を記録し、前回との差分から増加率を計算して
        日付・登録者数・増加率をJSONファイルに追記保存する
        また subscribe_client (YTSubscribeClient) が渡された場合は履歴も追加する
        :param count: 現在の登録者数
        :param date: 日付（デフォルトは現在日時）
        :param subscribe_client: YTSubscribeClientのインスタンス（連携用）
        """
        if not self._fetched:
            raise RuntimeError("fetch_current_subscribersを先に実行してください")
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        # 既存データを読み込み
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # 前回データがあれば増加率を算出
        if data:
            last = data[-1]
            last_count = last["subscribers"]
            last_date = datetime.strptime(last["date"], "%Y-%m-%d")
            days = (date - last_date).days or 1
            growth = (count - last_count) / days
        else:
            growth = 0  # 初回は増加率0

        # データを追記
        data.append({
            "channel_id": self.channel_id,
            "date": date_str,
            "subscribers": count,
            "growth_per_day": growth
        })

        # 保存
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # YTSubscribeClient との連携
        if subscribe_client is not None and hasattr(subscribe_client, "add_history"):
            subscribe_client.add_history(count, date)