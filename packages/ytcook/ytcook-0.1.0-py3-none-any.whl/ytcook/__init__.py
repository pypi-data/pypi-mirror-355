import browser_cookie3

def get_youtube_cookies():
    try:
        cj = browser_cookie3.load(domain_name='youtube.com')
        return cj
    except Exception as e:
        print(f"[ytcook] Error loading cookies: {e}")
        return None

def save_cookies_to_file(filename='cookies.txt'):
    cj = get_youtube_cookies()
    if cj is None:
        return False

    try:
        with open(filename, 'w') as f:
            for cookie in cj:
                f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\t{'TRUE' if cookie.secure else 'FALSE'}\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")
        print(f"[ytcook] Cookies saved to {filename}")
        return True
    except Exception as e:
        print(f"[ytcook] Failed to save cookies: {e}")
        return False