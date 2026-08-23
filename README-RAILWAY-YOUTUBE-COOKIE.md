# Railway YouTube Cookie Setup (GitHub + Railway only)

1. In Firefox, open the `cookies.txt` extension on youtube.com.
2. Choose **Current Site -> Download**.
3. Open the downloaded `cookies.txt` with a text editor/file manager and copy its entire text. **Do not send it to anyone.**
4. In Railway -> Variables -> New Variable, create:
   `YOUTUBE_COOKIES`
5. Paste the entire cookies.txt text as the value and save. Keep the variable private.
6. Redeploy the service.

The bot writes this value to `/tmp/youtube-cookies.txt` at runtime and passes it to yt-dlp. No cookies file needs to be committed to GitHub.

If the cookie expires, export a fresh one and replace the Railway variable.
