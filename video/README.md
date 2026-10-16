# Video of the website

The motion design video of the home page (about 78 s, 1920 × 1080, silent, French and English), written in HTML and
rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache 2.0): each scene is an HTML file
animated with GSAP, which HyperFrames captures frame by frame in headless Chrome and encodes with FFmpeg.

| File | Role |
| --- | --- |
| `STORYBOARD.md` | the direction and the nine scenes, beat by beat |
| `index.html` | the root: mounts the scenes back to back (`compositions/`), language variable |
| `compositions/NN-*.html` | one scene each |
| `assets/strings.js` | all the text, in French and English |
| `assets/theme.css`, `assets/wapp.js` | the website's design tokens; shared helpers and the network map |
| `assets/demo.json`, `assets/data.js` | the engine's demonstration day, and the map and examples drawn from it |
| `scripts/` | data export, one-scene test, render |

## Render

Requirements: Node.js 22, FFmpeg, Python with the repository's requirements (for `npm run data` only).

```bash
cd video
npm install                      # HyperFrames, GSAP, the fonts; copies the logo, patterns and photo from web/public
npx hyperframes browser ensure   # downloads Chrome Headless Shell (or set HYPERFRAMES_BROWSER_PATH)
npm run data                     # optional: recompute the demonstration day with the engine
npm run render                   # renders FR and EN, publishes web/public/video/*.mp4 and the posters
```

To work on one scene: `npm run scene -- 04-curves --lang en --at 2,6,11 --check` prints stills to look at;
`npx hyperframes preview` opens the whole video in the browser. A wording change only needs `assets/strings.js`
and a new render.

## Licences

The scenes, scripts and data are part of the repository (Apache 2.0 for the code, CC BY 4.0 for the data); the
rendered video is published under CC BY 4.0. Tools used and not redistributed here: HyperFrames (Apache 2.0),
GSAP (free "Standard" licence of GreenSock / Webflow), Roboto (Apache 2.0) and JetBrains Mono (SIL OFL 1.1) from
npm. Photo of scene 08: IAfrica76 (Innovation: Africa), CC0, Wikimedia Commons. Partner logos: their owners'.
