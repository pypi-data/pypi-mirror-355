import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class YTSubscribeClient:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.history = []  # [("YYYY-MM-DD", 登録者数)] のリスト（古い順）

    def add_history(self, count: int, date: Optional[datetime] = None):
        """
        履歴を追加するメソッド
        :param count: 登録者数
        :param date: 日付（datetime型、省略時は今日）
        """
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        # 重複日付の履歴は上書き
        self.history = [(d, c) for d, c in self.history if d != date_str]
        self.history.append((date_str, count))

    def predict_milestone_date(
        self, 
        target: int
    ) -> Optional[dict]:
        """
        登録者履歴から、指定した登録者数（target）到達日を予測します。

        :param target: 到達目標の登録者数
        :return: {"estimated_date": "YYYY年mm月dd日", "days_left": 残り日数, "slope": 1日あたり増加数, "intercept": 切片} 予測不能時はNone
        """
        history = self.history
        if len(history) < 2:
            return None

        dates = [datetime.strptime(d, "%Y-%m-%d") for d, _ in history]
        base_date = dates[0]
        days = np.array([(d - base_date).days for d in dates])
        subscribers = np.array([s for _, s in history])

        # 線形近似
        slope, intercept = np.polyfit(days, subscribers, 1)
        if slope <= 0:
            return None  # 伸びていない場合は予測不可

        days_to_target = (target - intercept) / slope
        estimated_date = base_date + timedelta(days=days_to_target)
        return {
            "estimated_date": estimated_date.strftime("%Y年%m月%d日"),
            "days_left": int(days_to_target),
            "slope": slope,
            "intercept": intercept
        }