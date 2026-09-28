# Share image and icons

Run these from the repo root. The page loads Fraunces and Courier Prime from Google Fonts, so it needs a network connection.

1. Render the master PNG (1200×630) from `og.html`:

   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
     --virtual-time-budget=8000 --window-size=1200,630 \
     --screenshot="$PWD/tools/og/og.png" "file://$PWD/tools/og/og.html"
   ```

2. Export the JPEG that `og:image` and `twitter:image` point to. It comes out around 150 KB. Some chat apps skip preview images much over 300 KB.

   ```bash
   python3 -c "from PIL import Image; Image.open('tools/og/og.png').convert('RGB').save('site/assets/img/og.jpg', quality=88, optimize=True, progressive=True, subsampling=0)"
   ```

3. Regenerate the icons from the Bake AI bread mascot (`tools/og/bakeai-bread.png`). This writes `favicon.ico`, `favicon-32x32.png`, `icon-192.png`, `icon-512.png` and `apple-touch-icon.png`:

   ```bash
   python3 tools/og/make_icons.py
   ```
