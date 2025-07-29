import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional, List, Dict, Any
from collections import Counter

class YTCommentClient:
    """
    YouTubeコメント取得・集計用クラス
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("環境変数 YOUTUBE_API_KEY が設定されていません")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        comments = []
        next_page_token = None
        try:
            while True:
                response = self.youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    maxResults=max_results,
                    pageToken=next_page_token
                ).execute()
                comments.extend(response['items'])
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            return comments
        except HttpError as e:
            print(f"コメント取得エラー: {e}")
            return []

    def count_comments_and_replies(self, video_id: str) -> Dict[str, Any]:
        comments = self.get_video_comments(video_id)
        total_comments = len(comments)
        total_replies = 0
        reply_authors = []
        for item in comments:
            reply_count = item['snippet']['totalReplyCount']
            if reply_count > 0 and 'replies' in item:
                for reply in item['replies']['comments']:
                    author = reply['snippet'].get('authorDisplayName', 'Unknown')
                    reply_authors.append(author)
                    total_replies += 1
        return {
            'total_comments': total_comments,
            'total_replies': total_replies,
            'unique_repliers': len(set(reply_authors)),
            'reply_authors': dict(Counter(reply_authors))
        }
