class YTStreamsClient:
    """
    YouTubeライブ配信関連の動画取得専用クラス
    """
    def __init__(self, youtube):
        """
        :param youtube: googleapiclient.discovery.buildで作成したYouTube APIインスタンス
        """
        self.youtube = youtube

    def get_upcoming_live_streams(self, channel_id: str, max_results: int = 10) -> list:
        """
        指定チャンネルの今後のライブ配信予定（未配信のライブ）一覧を取得する
        Returns: 動画情報リスト
        """
        from googleapiclient.errors import HttpError
        try:
            response = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                eventType='upcoming',  # これで「これから始まるライブ」のみに絞れる
                maxResults=max_results,
                order='date'
            ).execute()
            return response.get('items', [])
        except HttpError as e:
            print(f"ライブ配信予定取得エラー: {e}")
            return []