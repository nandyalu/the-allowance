# The social card

`og-image.png` is what Slack, Discord, X and LinkedIn show when somebody shares a link to the site. `frontend/src/index.html` points at it with `og:image` and `twitter:image`.

**It is a rendered file, and this folder is what renders it.** The picture carried the project name for a week after the rename, because it was a PNG with no source and nothing in a text search could find it.

To change it, edit `og.html` and run:

```sh
npm install playwright
node render.mjs "$PWD/og.html" ../../frontend/public/og-image.png
```

The page is 1200x630, which is the size every one of those services expects. It uses the site's own fonts from `frontend/public/fonts/` and the colour tokens from `frontend/src/theme.css`, so the card and the site cannot drift apart.
