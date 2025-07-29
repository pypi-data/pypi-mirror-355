import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional, Dict, Any, List

class YTVideoClient:
    """
    YouTube動画・チャンネル情報取得用クラス
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("環境変数 YOUTUBE_API_KEY が設定されていません")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.youtube.channels().list(
                part='snippet,contentDetails',
                id=channel_id
            ).execute()
            if response['items']:
                return response['items'][0]
            return None
        except HttpError as e:
            print(f"チャンネル情報取得エラー: {e}")
            return None

    def get_latest_video(self, channel_id: str) -> Optional[Dict[str, Any]]:
        info = self.get_channel_info(channel_id)
        if not info:
            return None
        uploads_playlist_id = info['contentDetails']['relatedPlaylists']['uploads']
        try:
            playlist_response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=1
            ).execute()
            if playlist_response['items']:
                return playlist_response['items'][0]['snippet']
            return None
        except HttpError as e:
            print(f"最新動画取得エラー: {e}")
            return None

    def get_video_statistics(self, video_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()
            if response['items']:
                return response['items'][0]['statistics']
            return None
        except HttpError as e:
            print(f"動画統計取得エラー: {e}")
            return None

    def get_videos_by_type(
        self, channel_id: str, max_results: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        指定チャンネルの動画を「ライブ配信アーカイブ」「通常動画」「Shorts」に分類して取得する

        Returns:
            {
                "live_archives": [...],
                "normal_videos": [...],
                "shorts": [...]
            }
        """
        import isodate

        def duration_to_seconds(duration: str) -> int:
            try:
                return int(isodate.parse_duration(duration).total_seconds())
            except Exception:
                return 0

        # まずアップロード動画のplaylistIdを取得
        channel_info = self.get_channel_info(channel_id)
        if not channel_info:
            return {"live_archives": [], "normal_videos": [], "shorts": []}
        uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']

        # プレイリストから動画ID一覧を取得
        video_ids = []
        next_page_token = None
        while True:
            try:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(max_results, 50),
                    pageToken=next_page_token
                ).execute()
            except HttpError as e:
                print(f"プレイリスト取得エラー: {e}")
                break
            for item in playlist_response.get('items', []):
                video_ids.append(item['snippet']['resourceId']['videoId'])
                if len(video_ids) >= max_results:
                    break
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token or len(video_ids) >= max_results:
                break

        # 動画情報を一括取得
        live_archives = []
        normal_videos = []
        shorts = []
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            try:
                videos_response = self.youtube.videos().list(
                    part='snippet,contentDetails,liveStreamingDetails',
                    id=','.join(batch_ids)
                ).execute()
            except HttpError as e:
                print(f"動画情報取得エラー: {e}")
                continue
            for video in videos_response.get('items', []):
                snippet = video.get('snippet', {})
                content_details = video.get('contentDetails', {})
                live_details = video.get('liveStreamingDetails', {})
                duration = content_details.get('duration', '')
                title = snippet.get('title', '').lower()
                width = snippet.get('thumbnails', {}).get('maxres', {}).get('width') or \
                        snippet.get('thumbnails', {}).get('standard', {}).get('width') or \
                        snippet.get('thumbnails', {}).get('high', {}).get('width')
                height = snippet.get('thumbnails', {}).get('maxres', {}).get('height') or \
                         snippet.get('thumbnails', {}).get('standard', {}).get('height') or \
                         snippet.get('thumbnails', {}).get('high', {}).get('height')

                # ライブ配信（アーカイブ含む）判定
                if live_details:
                    live_archives.append(video)
                # Shorts判定（60秒以下＆縦長 or タイトルに#shorts）
                elif (
                    duration and duration_to_seconds(duration) <= 60 and
                    ((height and width and height > width) or '#shorts' in title)
                ):
                    shorts.append(video)
                else:
                    normal_videos.append(video)

        return {
            "live_archives": live_archives,
            "normal_videos": normal_videos,
            "shorts": shorts
        }