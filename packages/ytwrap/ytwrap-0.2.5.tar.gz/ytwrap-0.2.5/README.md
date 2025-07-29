# ytwrap

[![PyPI version](https://img.shields.io/pypi/v/ytwrap.svg)](https://pypi.org/project/ytwrap/)
[![Python versions](https://img.shields.io/pypi/pyversions/ytwrap.svg)](https://pypi.org/project/ytwrap/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

YouTube Data API v3用Pythonラッパーです。

---

## インストール
```
pip install ytwrap
```

## 使い方
```python
import ytwrap

video = ytwrap.YTVideoClient()
comment = ytwrap.YTCommentClient()

# 例: 最新動画の取得
latest = video.get_latest_video('チャンネルID')

# 例: コメント集計
stats = comment.count_comments_and_replies('動画ID')
```

## 必要な環境変数
- `YOUTUBE_API_KEY` : Google Cloud Consoleで取得したAPIキー

## ライセンス
MIT

---

# English

A Python wrapper for the YouTube Data API v3.

## Installation
```
pip install ytwrap
```

## Usage
```python
import ytwrap

video = ytwrap.YTVideoClient()
comment = ytwrap.YTCommentClient()

# Example: Get latest video
latest = video.get_latest_video('CHANNEL_ID')

# Example: Analyze comments
stats = comment.count_comments_and_replies('VIDEO_ID')
```

## Required Environment Variable
- `YOUTUBE_API_KEY`: Your API key from Google Cloud Console

## License
MIT
