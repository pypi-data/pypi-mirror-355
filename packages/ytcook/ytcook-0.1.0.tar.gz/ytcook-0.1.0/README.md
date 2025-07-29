# ytcook

📦 A simple Python library to automatically extract YouTube cookies from your browser for use with `yt-dlp`.

## Installation

```bash
pip install ytcook
```

## Usage

```python
import ytcook

ytcook.save_cookies_to_file()  # Saves cookies to cookies.txt
```

You can now use it with `yt-dlp`:

```bash
yt-dlp --cookies cookies.txt https://youtube.com/watch?v=...
```