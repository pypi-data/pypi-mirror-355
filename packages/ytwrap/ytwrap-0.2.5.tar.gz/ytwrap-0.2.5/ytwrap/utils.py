from datetime import datetime
import pytz

class YTUtilsClient:

    # 日本時間（JST）に変換
    @staticmethod
    def to_jst(iso_timestamp, fmt="%Y-%m-%d %H:%M:%S"):
        """
        ISO形式のタイムスタンプをJSTに変換し、指定フォーマットで返す
        :param iso_timestamp: 例 '2025-06-12T10:00:00Z'
        :param fmt: 例 "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%m月%d日 %H:%M" など
        :return: フォーマット済みJST文字列
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        return dt.astimezone(jst).strftime(fmt)

    @staticmethod
    def to_jst_iso(iso_timestamp):
        """
        JSTのISO 8601形式（例: 2025-06-12T19:00:00+09:00）で返す
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        return dt.astimezone(jst).isoformat()

    @staticmethod
    def to_jst_short(iso_timestamp):
        """
        JSTの短い形式（例: 06/12 19:00）で返す
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        return dt.astimezone(jst).strftime("%m/%d %H:%M")

    @staticmethod
    def to_jst_ja(iso_timestamp):
        """
        日本語表記（例: 2025年06月12日 19時00分）で返す
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        return dt.astimezone(jst).strftime("%Y年%m月%d日 %H時%M分")

    @staticmethod
    def to_jst_weekday(iso_timestamp):
        """
        曜日付き（例: 2025-06-12(木) 19:00）で返す
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        w = ["月", "火", "水", "木", "金", "土", "日"]
        wd = w[dt.astimezone(jst).weekday()]
        return dt.astimezone(jst).strftime(f"%Y-%m-%d({wd}) %H:%M")

    @staticmethod
    def to_jst_timeonly(iso_timestamp):
        """
        時刻のみ（例: 19:00）で返す
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        return dt.astimezone(jst).strftime("%H:%M")

    @staticmethod
    def to_jst_custom(iso_timestamp, formatter):
        """
        JSTのdatetimeオブジェクトをユーザー定義の関数で任意の文字列に変換
        :param iso_timestamp: ISO形式のタイムスタンプ
        :param formatter: JSTのdatetimeを受け取り任意の文字列を返す関数
        :return: ユーザー定義のフォーマット文字列
        """
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        return formatter(dt.astimezone(jst))