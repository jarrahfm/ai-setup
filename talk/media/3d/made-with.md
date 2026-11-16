# How these 3D pictures were made

An AI agent (Mercury, a coding agent) wrote a Python script. The free 3D program Blender ran that script with no
window open, built the scene from it and drew every picture. No one modelled anything by hand. Made on
15 November 2026.

## Files in this folder

| File | What it is |
|---|---|
| `hammer_feather_moon.py` | The script. It builds the whole scene and renders it. |
| `turntable-sprite.jpg` | 36 views of the scene, camera circling it 10 degrees at a time, in one 6 x 6 picture (5760 x 3240, each view 960 x 540). About 2.0 MB. |
| `turntable-sprite.json` | Frame size, frame count, grid and order of the sheet. Frame 1 (top left) is the front view. |
| `hammer-feather-drop.mp4` | 3.0 s, 30 fps, 1280 x 720, H.264 (High), yuv420p, faststart, no sound. About 0.2 MB. |
| `hammer-feather-drop-poster.jpg` | Frame 1 of the clip: both objects held at 1.6 m. |
| `made-with.md` | This file. |

## What is in the scene

Grey Moon ground with craters and rocks, a black sky with stars, a small Earth, a low Sun with hard shadows. A
geology hammer and a feather held side by side at 1.6 m, with a striped 1.6 m rod between them (stripes every
0.2 m) and the label "1.6 m".

In the clip the two objects hang still for 0.5 s, are let go together, fall together and land together 1.40 s
later. A faint copy is left every 0.2 s, like the 2D page in the talk. After landing each object tips onto its
side.

## Where the numbers come from

- Release height 1.6 m: NASA Science, "The Apollo 15 Hammer-Feather Drop",
  https://science.nasa.gov/resource/the-apollo-15-hammer-feather-drop/ ("approximately 1.6 m").
- Moon surface gravity 1.624 m/s2: NASA Science, "Compare Earth and the Moon",
  https://science.nasa.gov/moon/by-the-numbers/.
- Both are copied from `.mercury/short-talk/hooks-v2/spec.md`, which quotes the sources. They were not re-read
  for this file.
- Height above the ground t seconds after release: 1.6 - 1.624 x t x t / 2. Time to land:
  square root of (2 x 1.6 / 1.624) = 1.404 s. In the clip the objects are let go at 0.5 s and touch the ground in
  frame 59 (1.933 s); in frame 58 they are 8 mm above it.

What is not measured, and was chosen by eye:

- The tip-over after landing.
- The shapes and sizes of the hammer and the feather (simple models, not copies of the Apollo 15 objects).
- The craters, rocks, stars and the Earth's land and clouds (random patterns).
- The Earth is drawn about twice as wide as it looks from the Moon, so it shows on a projector. (From the same
  NASA page: 12,742 km Earth diameter / 384,400 km distance gives about 1.9 degrees; the picture uses about 3.8.)

## Blender: which one and where it came from

- Blender 4.2.2 LTS (build hash c03d7d98a413, build date 2024-09-24), from the "blender-v4.2-release" branch.
- Already on this computer at `C:\DDayDrive\Blender\blender.exe`, found through the Start Menu shortcut
  "Blender 4.2". Nothing was downloaded or installed, and no setting was changed. The `--factory-startup` flag makes
  Blender ignore its saved preferences.

## Command lines

Run from any folder; `OUT` is a folder for the frames.

```
blender.exe --background --factory-startup --python hammer_feather_moon.py -- turntable OUT 96
blender.exe --background --factory-startup --python hammer_feather_moon.py -- drop OUT 96
```

Then ffmpeg (version 2023-09-07, gyan.dev build) packed the frames:

```
ffmpeg -framerate 1 -i OUT/turn_%02d.png -vf tile=6x6 -frames:v 1 -q:v 4 turntable-sprite.jpg
ffmpeg -framerate 30 -i OUT/drop_%04d.png -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an hammer-feather-drop.mp4
ffmpeg -i OUT/drop_0001.png -q:v 3 hammer-feather-drop-poster.jpg
```

For a quick check before a long render, the script also has `still` (one frame) and `dropcheck` (four frames).
Add `cpu` as a fourth word to render without the graphics card.

## Render settings

- Engine: Cycles, 96 samples per pixel, OpenImageDenoise, at most 4 light bounces. Colour: AgX, "Medium High
  Contrast".
- Device: the laptop's NVIDIA GeForce RTX 3060 Laptop GPU through OptiX. The script uses a graphics card if it
  finds one, otherwise the processor.
- Turntable: 960 x 540, 36 frames, 24 mm lens, camera 2.5 m from the rod at 1.4 m height.
- Drop: 1280 x 720, 90 frames at 30 fps, 30 mm lens, camera 3.1 m in front at 0.8 m height.

## How long it took

- Turntable, 36 frames: 147 s in total on the graphics card (about 4 s a frame).
- Drop, 90 frames: 564 s in total on the graphics card (about 6 s a frame).
- One turntable frame on the processor only (Intel Core i7-12650H, `cpu` option): 24 s. So on a laptop without a
  suitable graphics card, expect roughly 15 minutes for the turntable and about an hour for the drop. Only that one
  processor frame was timed; the rest is an estimate.
- Before the final renders the agent made several rounds of test frames, looked at each picture, and changed the
  script: darker ground, camera lower so the objects stand against the black sky, the hammer and feather turned to
  face the camera, the rod moved between them, the "1.6 m" label turned to face the camera, the hammer head made
  thicker.
- The script was edited once after the final renders (the `cpu` option and comments only). A test frame from the
  edited script matched the final turntable frame 1 (PSNR 90 dB).

## The request a teacher could give an AI agent

> Write a Python script for Blender 4.2 that I can run with "blender --background --python". It should build a
> simple, clean scene of the Moon's surface: grey ground with a few craters, a black sky with stars and a small
> Earth. Put a hammer and a feather side by side, held 1.6 m above the ground, with a striped 1.6 m pole between
> them. Light it with one low Sun so the shadows are sharp. Render two things: 36 pictures with the camera going
> round the scene, and a 3-second video at 30 frames a second where both objects are let go together and fall
> with the Moon's gravity, 1.624 m/s2, so they land together after about 1.4 seconds. Use the graphics card if
> there is one. Put the numbers at the top of the script, and tell me how to check one picture before the long
> render.
