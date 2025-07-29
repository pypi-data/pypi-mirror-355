import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class YTSubscribeClient:
    """
    YouTubeチャンネル登録者数の予測・解析用クライアント
    """
    def __init__(self):
        pass

    def predict_milestone_date(
        self, 
        history: List[Tuple[str, int]],  # 例: [("2025-06-01", 8000), ...]
        target: int
    ) -> Optional[dict]:
        """
        登録者履歴から、指定した登録者数（target）到達日を予測します。

        :param history: [("YYYY-MM-DD", 登録者数)] のリスト（古い順）
        :param target: 到達目標の登録者数
        :return: {"estimated_date": "YYYY-MM-DD", "days_left": 残り日数, "slope": 1日あたり増加数, "intercept": 切片} 予測不能時はNone
        """
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