# Piloting a Generative Cinépoème from Claude Code

🇫🇷 [Version française](./README.fr.md)

## The mission

The idea pre-existed. The execution had hard time boxes:

- **48 hours, full**, to write the text (one long-form narrative voiceover, in French, then translated to English for voice cloning).
- **24 hours, full**, to produce the film from that text: image generation, voice cloning, image-to-video, music, sound design, audio mix, edit, subtitles, upload, delivery to a venue.

No team. One filmmaker, one Mac, one prompt window. Delivery deadline non-negotiable (a venue vernissage that same evening).

These are method notes from that 24-hour film-production sprint piloted entirely from **Claude Code** (Anthropic's CLI) and a **Claude AI Project**.

The film itself is not the subject here. The **method** is.

---

## The setup

- **Claude Code CLI** (mac terminal) as the main cockpit — everything flows through it: image generation, image-to-video, voice cloning, TTS, music, sound design, audio mix, ffmpeg editing, subtitles, upload, email delivery.
- **Claude AI Project** (web) as **external memory**: pitch, references, mood, EDLs of the five editors invoked as agents (Murch, Marker, Schoonmaker, Pagh Andersen, Baxter). The project acts as the persistent "bible" that the CLI reads on session start.
- **Sub-agents** (`/agents`) for tasks that need an isolated context: a "pool visual analysis" agent (frame extraction + Claude vision), five "editor" agents each producing their own distinct EDL, a "pool audit" agent that tags each shot FIDELE / BUG / DOUBLON.
- **Background tasks** (`run_in_background`) to parallelize generation + build + upload without blocking the conversation.

---

## The pipeline (operation order)

1. **Source image** — ChatGPT image (gpt-image-1) generates a pool of PNGs from iterative prompts. Output: ~120 PNGs on local disk.
2. **CDN upload** — each PNG uploaded to **fal storage** (free, works even when fal generation is locked — handy). Public URL consumable by any i2v platform.
3. **Image-to-video** — Seedance 2.0 via two platforms in parallel (fail vs win, see below).
4. **Voice cloning** — clean audio sample uploaded, voice_id generated, TTS with that voice_id. The result outclasses every generic TTS available — it's the **only way** to get a recognizable signature timbre.
5. **Music** — drone ambient + hauntology + club, three tracks generated separately, mixed in layers.
6. **Live ffmpeg audio mix** — VO + drone + accents + club, moderate ducking via fixed levels (sidechain compression tried then simplified).
7. **ffmpeg edit** — `concat demuxer` for hard cuts, `setpts` for moderate slow, `minterpolate` for smoothing.
8. **Subtitles** — local whisper.cpp → SRT EN → manual FR translation → ASS/SRT → burn via libass (requires a "full" ffmpeg build).
9. **Upload + send** — Google Drive via `gws` CLI, public link, email sent via mail-cli from Claude Code.

---

## Voice cloning > generic TTS

Every TTS tested (ElevenLabs v3 with `[breath]` `[tearful]` tags, calm voices Sarah / Matilda / River / Charlotte / Bianca / Alice) sounds **"highschool drama"**. The voice fails to carry the text, the ear disengages.

**Voice cloning** of a cinema-grade voice (signature timbre, recognizable inflection, natural prosody) on 75 seconds of clean sample = category shift. The clone reproduces what TTS cannot: the breath between phrases, the vocal tell, the grain.

Three lessons:
- **Clean sample mandatory**: a sample where the target voice speaks alongside another voice contaminates the clone (it drifts toward a mixed/masculinized voice). Always isolate a monophonic extract.
- **One single clone for the whole film** beats four mood-matched clones. Mood shifts happen through speed parameters and natural prosody, not through vocal mosaic.
- **Replicate `minimax/voice-cloning`** or **fal MiniMax**: quality-equivalent, ~$3 per clone + $0.05 / 1k chars.

---

## Technical fails

### fal.ai: locked account despite positive balance
After top-up, the lock flag is not cleared infra-side. Support tickets unanswered. Storage keeps working (uploads OK) but generation is blocked. **Any pipeline depending on a single provider is fragile.**

### PiAPI: User-Agent ban + 2 concurrent jobs limit
- ffmpeg CLI then `urllib.request` Python = User-Agent `Python-urllib` blacklisted by Cloudflare → systematic HTTP 403. Patch: header `User-Agent: Mozilla/5.0...`.
- PiAPI's basic plan = hard limit of **2 active tasks** at once. The launcher must submit, wait, submit next. For 17 shots at 2-3 min each, this gives ~40 min of queue.
- Zombie tasks block the slots (`pending` never resolved) — you need a DELETE endpoint to cancel.

### Krea exposes Seedance via UI but not via MCP
The official Krea MCP only exposes Seedance 1.0. Version 2.0 is only accessible via the web interface — so usable from Claude Code only through **Playwright / Browser Use** (web automation), not via direct CLI. Slows the pipeline.

### Video looping in ffmpeg = perceived false repetitions
To match the VO duration when image material was short, I looped the video (`-stream_loop -1`). Disaster: the viewer sees the first shots reappear = perceived as "broken intentional repetitions". Clean fix: **increase global slowdown** or **add more material**, don't loop.

### Prompt ↔ image mapping mismatch
When you identify 17 PNG timestamps via a quick batch Read, similar frames get confused easily. A prompt "top-down mechanical hand over eyes" applied to an image that actually contains "Mira lying on an alligator" produces a mixed hallucination. **Visual audit mandatory**: extract one frame per shot, read with a vision agent, tag.

### libass missing from default brew ffmpeg
`brew install ffmpeg` (8.x) doesn't include `libass` — so the `subtitles=*.srt` filter returns `No option name near`. You need `ffmpeg-full`, which compiles with `--enable-libass`. Misleading symptom: ffmpeg "works" for everything except subtitle burning.

### Whisperx → transformers import error
`whisperx` breaks regularly on the `Wav2Vec2ForCTC` import when transformers updates. Fallback: **whisper.cpp** via `whisper-cli` (Apple Silicon native, GGUF model).

---

## Technical wins

- **Parallel background tasks**: 4 ffmpeg builds in parallel + PiAPI batch + 5 editor agents simultaneously, without blocking the main session.
- **Sub-agents for visual analysis**: a dedicated agent extracts frames from 50+ rushes, analyzes them with Claude vision, writes an audit MD with FIDELE/BUG/DOUBLON tags. Saves 30+ min of manual review.
- **Single-pass audio mix**: `ffmpeg -i vo -i drone -i accents -i club -filter_complex "amix=inputs=4..."` produces the full mix in one process.
- **Inter-provider pivot without loss**: storage CDN on fal (free) + generation on PiAPI (independent account), public URLs work regardless of which i2v platform consumes them.
- **Email + Drive from CLI**: `gws drive +upload` + `mail-cli` = public Drive link generated + email sent to recipients in two commands.

---

## Artistic wins

- **Editor council**: pushing five editor-agents (Murch / Marker / Schoonmaker / Pagh Andersen / Baxter) to each propose their own distinct EDL on the same pool reveals **structural disagreements** that are the very subject of the film (e.g., Schoonmaker values the neon aquarium shots as oneiric, Pagh Andersen bans them as capitalist mirages). That disagreement becomes editing material.
- **Voice-cloning a signature timbre** (vs generic TTS) shifts the material from amateur side-project to a film that can hold up before a programming committee.
- **Moderate slow 1.5-1.8x** on contemplative shots = subtle visual signature, oneiric, without becoming "advertising slow-motion".
- **FR burned subtitles** transforms a bilingual/anglophone object into a French-receivable object for francophone programming.

---

## Comparison: editing with ffmpeg vs piloting an NLE

### Option A — ffmpeg only (this pipeline)

**For:**
- No license, no GUI, infinitely scriptable.
- Reproducible: the same script produces the same edit with a different seed.
- Parallel background tasks: 4 edits at once, impossible in an NLE.
- No dependency on a high-GPU Mac — runs anywhere, even a Mac mini.
- Zero cost.

**Against:**
- No timeline visualization. You compose blind.
- Slow iterations: every shot-duration change = full re-render.
- No morph cut, no stabilization, no automatic masking.
- Audio mix limited to `amix` + `sidechaincompress` — no visual EQ, no easy spatial mix.
- Subtitle styling hard without libass + well-formed ASS.

### Option B — Pilot Final Cut Pro from Claude Code

Exists: **SpliceKit** (in-process dylib JSON-RPC injected into FCP), accessible via MCP. Method used by some "AI-native" filmmakers. Lets Claude Code open an FCP project, blade, move clips, add effects, export.

**For:**
- Native timeline visualization.
- Effects / color grade / masks / morph cuts professional.
- Powerful audio mix via FCP plugins.
- Native sub-burn via FCP-generated captions.
- Known cinema post-production workflow.

**Against:**
- FCP must run in parallel, consumes RAM / GPU on the same Mac.
- The SpliceKit MCP needs specific setup, can break on FCP updates.
- Not reproducible: an FCP project isn't re-runnable from a script like a `.sh` ffmpeg.
- FCP license cost.

### Option C — Pilot DaVinci Resolve from Claude Code

DaVinci Resolve exposes an official Python API (`DaVinciResolveScript`). Allows: open project, import clips, create timeline, blade, effects, color, deliver.

**For:**
- Stable, documented official API.
- Reference color grading (Resolve is the cinema standard).
- Fusion integrated for complex compositing.
- Powerful free tier.

**Against:**
- Python API to call from Claude Code = another indirection.
- Heavy GUI workflow, Resolve consumes enormous RAM / GPU.
- Slow to boot, not ideal for fast iteration.

### Option D — Pilot Premiere Pro from Claude Code

Exists via **Adobe MCP** ("adb-mcp", 5 servers: Photoshop / Premiere / InDesign / After Effects / Illustrator). Premiere accessible via UXP scripts from Claude Code.

**For:**
- Familiar professional workflow.
- Rich ExtendScript / UXP, many functions exposed.
- After Effects integration for VFX.

**Against:**
- Adobe = subscription.
- Premiere notoriously unstable on long projects.
- The UXP API is less mature than Resolve / SpliceKit FCP.

### Option E — CapCut / iMovie / InVideo

CapCut: no serious public API. Pilot via UI automation (Playwright on web app).
iMovie: limited AppleScript, not pro.
InVideo: web SaaS, automatable via Playwright, but free tier has duration / resolution / watermark limits.

**Verdict: useful only for high-volume templates or social media output, not for a cinépoème.**

---

## Comparison: AI generation platforms

| Platform | Image | i2v | Voice clone | Music | CLI/API | Notes |
|---|---|---|---|---|---|---|
| **fal.ai** | Flux, etc. | Seedance 2 | MiniMax | Stable Audio | Rich API | Fragile account (locks even with positive balance) |
| **Replicate** | Flux | Seedance 1 Pro | MiniMax | Lyria, ACE | Stable API | Pricier but reliable |
| **PiAPI** | — | Seedance 2 | — | — | Cloudflare WAF API, 2-job limit | User-Agent ban |
| **Krea** | Krea models | Seedance 2 (UI only) | — | — | MCP exposes only Seedance 1 | Playwright for Seedance 2 |
| **ChatGPT image (gpt-image-1)** | OK | — | — | — | OpenAI API | Reference for image pool |
| **Higgsfield** | — | i2v | — | — | CLI? | Not tested this session, worth checking |
| **ElevenLabs** | — | — | Voice clone + Music | Music v3 | Stable API | Generic TTS unconvincing for cinema |
| **MiniMax** | — | — | speech-02-hd | Music v2.6 | Via fal or Replicate | Best voice clone tested |
| **Suno** | — | — | — | Music | API | Not explored this session |

**Practical recommendation**: use **fal storage** for public CDN (free, reliable even with locked account), **PiAPI or Replicate** for main generation (two providers as backup), **MiniMax via Replicate** for voice cloning, **Lyria via Replicate or ElevenLabs Music** for music. **Never** depend on a single provider.

---

## Lessons learned

1. **Voice cloning > TTS** for any serious narrative project. The crossing isn't optional.
2. **Public CDN storage separate from the generation account** = resilience.
3. **Automated visual rush audit** before editing = massive time gain.
4. **Sub-agents for specialized tasks** (analysis, EDL, audit) rather than one monolithic mega-prompt.
5. **Parallel background tasks** for anything that can run while you think.
6. **Do not loop video to match audio** — prefer moderate slowdown or more material.
7. **ffmpeg to iterate fast, NLE to finalize** if visual complexity demands it.
8. **Always visually validate each generated shot** before integration — AI hallucinates regularly and visual bugs (yo-yo in a speaker pod, cross in the sky, smartphones in 2095) are recurring.
9. **Show every email draft to the author** before sending — the CLI pipeline can send instantly, and that's precisely why you must enforce a human checkpoint.

---

## Tools used (summary)

**CLI / dev**: Claude Code (Anthropic), `gh`, `gws`, `mail-cli`, `gdrive`, `rclone`, `whisper-cli` (whisper.cpp), `ffmpeg`, `ffmpeg-full` (libass), `python3`, `curl`.

**AI platforms**: ChatGPT (image), fal.ai (storage + i2v + clone, lockable), Replicate (i2v + clone + music, reliable), PiAPI (Seedance 2 i2v, Cloudflare-protected), Krea (web i2v), ElevenLabs (TTS + music), MiniMax (voice clone).

**Models**: Seedance 2.0 (ByteDance i2v), MiniMax speech-02-hd (voice clone), Lyria 2 / Stable Audio 2.5 (music), Whisper small (transcription).

**Notable MCPs**: Adobe (Photoshop / Premiere / AE / Illustrator / InDesign), SpliceKit (FCP), Playwright, Pinecone, clipboard-vision, comfyui, Krea, Beeper, Postiz.

**Process**: Claude Code sub-agents (invoked editors, pool analysis, audit), background tasks, Claude AI Project (external memory: pitch + EDLs + references).

---

## Coda

This repo is a method note, not a turnkey production kit. Every film has its own pipeline. The central takeaway of this session: **piloting a complete production chain from Claude Code is feasible and fluid for a filmmaker who knows what they want**, provided you accept three trade-offs:

- Slower fine-tuning iterations vs an NLE
- No timeline visualization during ffmpeg editing
- Dependency on fragile external platforms (locks, rate limits, API changes)

The gain: reproducibility, parallelism, traceability, and most of all — **staying in one mental environment** for 12 hours of production, without context-switching between 6 applications.

---

*Notes taken the day after a ~12h session; to be expanded on future projects.*
