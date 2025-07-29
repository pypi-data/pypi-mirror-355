import ytwrap

CHANNEL_ID = "UCYrHEsf7bhiFJssY5btS7Zg"

def main():
    video_client = ytwrap.YTVideoClient()
    comment_client = ytwrap.YTCommentClient()

    # 最新動画取得
    latest_video = video_client.get_latest_video(CHANNEL_ID)
    if not latest_video:
        print("動画が見つかりませんでした")
        return
    video_id = latest_video['resourceId']['videoId']
    video_title = latest_video['title']
    published_at = latest_video['publishedAt']

    # 動画統計
    video_stats = video_client.get_video_statistics(video_id)
    api_comment_count = int(video_stats.get('commentCount', 0)) if video_stats else 0

    # コメント集計
    comment_stats = comment_client.count_comments_and_replies(video_id)

    print(f"動画タイトル: {video_title}")
    print(f"公開日: {published_at}")
    print(f"API取得コメント総数: {api_comment_count}")
    print(f"実際に分析したコメント数: {comment_stats['total_comments']}")
    print(f"総返信数: {comment_stats['total_replies']}")
    print(f"返信者数: {comment_stats['unique_repliers']}")
    print(f"返信者ランキングTOP3: {sorted(comment_stats['reply_authors'].items(), key=lambda x: x[1], reverse=True)[:3]}")

if __name__ == "__main__":
    main()
