# Piloting Generative Film Production from Claude Code

A method note from a filmmaker (Ismaël Joffroy Chandoutis) running the entire production chain of a short generative film through a Claude Code CLI cockpit + a Claude AI Project writer's room.

🇫🇷 [Version française](./README.fr.md)

> The film itself isn't the subject here. The **method** is. The repo is meant for filmmakers, AI engineers, and researchers thinking about how an artist can keep ownership of vision while delegating execution to an agent team.

---

## 1. The mission

The idea pre-existed. Hard time boxes:

- **48 hours, full** to write the text (long-form narrative voiceover, FR, then translated EN for voice cloning).
- **24 hours, full** to produce the film: image generation, voice cloning, image-to-video, music, sound design, audio mix, edit, subtitles, upload, delivery to a venue.

One filmmaker. One Mac. Non-negotiable vernissage deadline.

These notes don't tell a clean story. They tell what **actually happened**: 60% of the value came from method, 40% from crisis management. Both are documented.

---

## 2. The mental architecture (corrected)

Two distinct Claude instances, two distinct purposes.

### Claude AI Project (web) = The writer's room — **48h, text only**

- Two browser windows open in parallel.
- **Head** : a Claude that judges, critiques, structures. Reads a fragment, says what's missing, what to cut, what's true.
- **Arms** : a Claude that writes, drafts, extends. Receives instruction from Head and generates.
- The filmmaker is the **switchboard** between Head and Arms. Never write and judge in the same session — split it.
- The Project's "knowledge" pane carries the bible (pitch, references, mood, prior drafts) so both windows share state.

### Claude Code CLI (terminal) = The production studio — **24h, everything else**

- Not a film-specific setup. The filmmaker arrives with a **harness** — their general filmmaker config — global CLAUDE.md, custom skills, agent registry, MCPs, shell aliases. The studio works for any film, not just this one.
- Provides multi-agent execution: a director agent (the filmmaker's vision), a team of specialized sub-agents (worldbuilder, storyboard, generation director, editor council, audio engineer, audit, delivery).
- Switching between Claude Project (web) and Claude Code (CLI) **changes the kind of answer you get**. Web Claude is more reflexive, more critical, slower. CLI Claude is more executive, more shell-aware, accepts more lateral tools. Knowing when to switch is half the method.

### Why the split matters

- The Project keeps the text inviolate; the CLI never modifies the source narrative.
- The CLI consumes the text as input — it's read-only there.
- Iteration on the text happens in the Project, iteration on the production happens in the CLI. They never cross-contaminate.

### Cognitive mode selection in Claude Code

- **Adaptive think mode** when you have ambiguity / open creative problem.
- **Off-think mode** when you're driving a deterministic pipeline (ffmpeg, file ops, transcoding). Faster.
- **Sonnet** for speed flow, large parallel sub-agents, throughput-bound tasks.
- **Opus** for the council (multi-perspective editing analysis), the auteur agent, the final synthesis. Quality-bound tasks.

This isn't optional. Wrong mode = wasted minutes per turn × hundreds of turns = lost hours.

---

## 3. The team agent

Claude Code as a multi-agent shop. Each sub-agent has its own context, prompt, and tool-set. The orchestrator (you in the main CLI session) hands off concerns, waits for results, integrates.

| Agent | Role | When invoked | Output |
|---|---|---|---|
| **Director (master)** | Holds the filmmaker's vision. Routes. Says yes/no. | Always (main session). | Decisions. |
| **Worldbuilder** | Generates character sheets, locations, props, color palettes, mood boards. | Pre-production. | Asset library. |
| **Storyboard** | Generates vignettes with captions for each beat. | Pre-production. | Storyboard.md + image refs. |
| **Asset Manager** | Uploads to CDN, organizes the pool, dedups, tags. | Throughout. | Asset index. |
| **Generation Director** | Picks model + resolution + mode per shot based on budget/quality target. | Per shot. | Generation plan JSON. |
| **Editor Council** | 5 named editor personas (Murch, Marker, Schoonmaker, Pagh Andersen, Baxter) producing parallel EDLs. | Editing phase. | 5 distinct EDLs. |
| **Edit Engineer** | Builds the actual montage from the chosen EDL via ffmpeg. | Editing. | montage.mp4. |
| **Audio Engineer** | Music selection, mix, mastering. | Post-prod. | audio.m4a. |
| **Subtitle Engineer** | Whisper transcript → translation → ASS burn. | Post-prod. | subs.srt + burned mp4. |
| **Audit (QA)** | Per-shot quality check, hallucination detection, doublon detection. | Per asset generated. | Tag MD (FIDELE/BUG/DOUBLON). |
| **Delivery** | Upload, share link, email composition + send. | End. | Sent email. |
| **Cost Tracker** | Watches spend across all platforms; alerts on threshold. | Throughout. | Budget log. |

**Critical design choice** : sub-agents have **isolated context**. They don't see the full conversation, they see only their brief. This prevents context bleed and forces the orchestrator to write clean briefs — which is the discipline that makes the system work.

---

## 4. Worldbuilding methodology

This is the order of operations that emerged. Each step has a deliverable.

### Step 1 — Text (in Claude AI Project, 48h)
- Long-form narrative VO, voice = the protagonist or a third-person narrator.
- Output : `script.md` (in Claude Project knowledge pane).

### Step 2 — Color palette
- 3-5 dominant tones + 1-2 accent colors.
- Approach: ask the worldbuilder agent to propose palettes from the script's mood, then validate via reference image search.
- Output : `palette.md` with hex codes + reference images.

### Step 3 — Character sheets (LoRA training data)
- 5-10 angles per main character (front, 3/4, profile, back, close-up, full body, expressive states).
- Approach: Krea 2 with consistent seed + character prompt, then iterate angle-by-angle. Optional: train a LoRA on the 5-10 images using Flux 2 / Z Image / Krea 2 LoRA training. The LoRA becomes the character's stable identity across all subsequent generations.
- Output : `characters/<name>/sheet_*.png` + `characters/<name>/lora.safetensors` (optional).

### Step 4 — Locations / décors
- 3-5 key views per location (establishing wide, medium, close, lighting variation, time-of-day variation).
- Approach: GPT Image 2 for hero locations (precise prompt following), Krea 2 for ambient / atmospheric variations.
- Output : `locations/<name>/view_*.png`.

### Step 5 — Props / artifacts
- Reference shots of key objects (the speaker, the urn, the laptop, the artifact that drives the plot).
- Same approach as locations.
- Output : `props/<name>.png`.

### Step 6 — Storyboard vignettes
- 1-3 vignettes per beat. A beat = a sentence or paragraph from the script.
- Each vignette has: caption (what's happening) + reference image (generated still) + camera direction (static / slow drift / pan) + duration target + audio cue + color palette tag.
- Approach: a dedicated `storyboard` sub-agent reads the script + the worldbuilder's output, proposes vignettes, generates draft images via Krea 2.
- Output : `storyboard.md` + `storyboard/<beat_id>_v*.png`.

### Step 7 — Generation pool expansion
- Each storyboard vignette spawns 3-5 alternative source images (different framings, light variations).
- This pool exists to give the editor room to choose, not to dilute.
- Approach: Krea 2 batch + GPT Image 2 for hero shots only.
- Output : `pool/<beat_id>_v*.png` (typically 100-200 PNGs for a 10-min film).

### Step 8 — Image-to-video generation
- 80% of the pool : LTX 2.3 (fast, local or via fal, $0.02-0.05 per shot in cloud, $0 local).
- 20% (hero shots, the 15-20 visible "key" moments) : Seedance 2 Pro 1080p ($0.65-1.04 per shot).
- Mode: image-to-video (i2v). The PNG drives frame 0; the prompt drives motion. This preserves the worldbuilder's art direction.
- Output : `rushes/<beat_id>.mp4` (each 4-8s).

### Step 9 — Audit + selection
- Audit sub-agent extracts a frame at mid-duration from each rush, reads with vision, tags FIDELE / BUG / DOUBLON.
- Bugs (hallucinations: extra arms, smartphones in a post-2090 world, crosses appearing in skies) go to quarantine.
- Doublons (visual duplicates of same scene) are deduplicated keeping the best.
- Output : `audit.md` + `pool_validated/` + `pool_quarantine/`.

### Step 10 — Edit + mix + subs + deliver
- Editor council produces 5 EDLs in parallel.
- Director picks one or composes a synthesis.
- Edit engineer builds the master via ffmpeg.
- Audio engineer mixes VO + drone + accents + spotlight tracks.
- Subtitle engineer generates SRT, translates, burns.
- Delivery agent uploads, generates link, drafts email, waits for filmmaker confirmation, sends.

---

## 5. The 80/20 model selection strategy

Rule of thumb: use cheap/fast for **80% iteration**, premium for **20% final**.

### Image generation

| Use case | 80% (draft, iterate, moodboard) | 20% (final, hero) |
|---|---|---|
| **Concept moodboard** | Krea 2 (Midjourney-style, fast) | — |
| **Character sheets** | Krea 2 with seed | GPT Image 2 for key portraits |
| **Locations** | Krea 2 | GPT Image 2 (precise prompt) |
| **Storyboard vignettes** | Krea 2 batch | GPT Image 2 for the 5-10 hero stills |
| **LoRA training data** | Flux 2 / Z Image / Krea 2 LoRA pipelines | — |
| **Image editing (inpaint, modify)** | Gemini 2.x / 3.x Flash "nano banana" (multimodal edit) | Photoshop manual if needed |

**Why this split** : Krea 2 hits a sweet spot of speed, quality, and cost — perfect for the 100-200 source images you'll generate. GPT Image 2 (released early 2026) follows complex prompts faithfully and excels at compositions with text or precise spatial layouts — reserve for the 5-10 hero shots where prompt fidelity matters most.

**Gemini Flash "nano banana"** : the image-editing multimodal mode is the closest thing to "Photoshop light" via API. Use it for: inpainting unwanted objects, adjusting color cast on a single asset, restyling a character's outfit without regenerating the entire shot.

### Image-to-video

| Use case | 80% (iteration, pool, rushes) | 20% (final hero shots) |
|---|---|---|
| **General i2v** | **LTX 2.3** (Lightricks open-source, local or hosted) | **Seedance 2 Pro** |
| **First-last frame transitions** | LTX 2.3 conditional input | Seedance 2 (first_last_frames mode) |
| **Long shots (>8s)** | Hunyuan Video (local) or Wan Video 2.1 | Seedance 2 Pro |
| **High-motion / action** | LTX 2.3 (good at motion) | Seedance 2 Pro 30fps |
| **Cinematic atmospheric** | LTX 2.3 | Seedance 2 Pro |

**Resolution / FPS economics (Seedance 2 reference)** :

| Resolution | FPS | Cost / sec | Use case |
|---|---|---|---|
| 480p | 24 | $0.06 | Test only |
| 720p | 24 | **$0.10 (fast)** | Pre-viz, rushes |
| 1080p | 24 | **$0.13 (pro)** | Final |
| 1440p+ | 30 | $0.20+ | Cinema hero only |

**t2v vs i2v vs v2v decision tree** :
- **i2v** = default. Image fixes frame 0 → preserves art direction → coherent across shots.
- **t2v** = only for abstract / transitional / non-character moments. Risk: hallucination drift.
- **v2v** = style transfer on existing footage. Use rarely (Runway Gen-4 v2v, Pika, etc.). Expensive and tricky.

**Recommendation** : i2v as default, t2v only when text prompt is the entire shot (e.g., abstract logo morphs), v2v almost never.

### Voice

- **TTS generic** (ElevenLabs voices, OpenAI TTS) = **don't use for narrative cinema**. Sounds like a podcast intro at best. Voice cloning is the only viable path for cinéma d'auteur.
- **Voice cloning** : MiniMax `speech-02-hd` via Replicate (`minimax/voice-cloning` → `minimax/speech-02-hd`). ~$3 clone + $0.05 / 1k chars. Clean 75s sample mandatory.
- **ADR / foley / SFX** : ElevenLabs SFX (text-to-audio for non-musical sound effects).
- **Critical lesson** : ONE clone for the entire film. Mood shifts come from `speed` parameter + natural prosody, not from a mosaic of mood-matched clones (tested, sounds like multiple people).

### Music

| Use case | Model | Provider | Notes |
|---|---|---|---|
| **Drone / ambient bed** | Lyria 2 | Replicate | Best for sustained pads, cinematic tension |
| **Hauntology / synthwave** | ElevenLabs Music v3 | ElevenLabs | Good genre control |
| **Score / orchestral** | MiniMax Music v2.6 | Replicate | Decent for short cues |
| **Club / dance** | ElevenLabs Music v3 | ElevenLabs | Use with low-pass filter for "muffled / heard from outside" |
| **Stable Audio 2.5** | — | fal | Tested, weaker than Lyria for drone |

Layer 2-4 tracks for richness. Drone constant low (-22 to -28 dB), accents punctual mid, club only on spectacle scenes.

### Audio mix

**Why ffmpeg and not Logic Pro / Audacity / Pro Tools** :

| | ffmpeg | Logic Pro | Audacity | Pro Tools |
|---|---|---|---|---|
| Scriptable | ✅ Full | Partial (AppleScript / Scripter MIDI) | Partial (Nyquist) | Limited |
| Reproducible | ✅ Same script = same output | ❌ Project file required | ❌ | ❌ |
| Parallel runs | ✅ N background processes | ❌ Single instance | ❌ | ❌ |
| License | Free | $200 | Free | $600+/year |
| Multi-track mix | ✅ `amix=inputs=4` | ✅ Visual mixer | Limited | ✅ Best |
| Visual EQ / spatial | ❌ | ✅ | Partial | ✅ |
| GPU-accelerated reverb | ❌ | ✅ | ❌ | ✅ |
| Sidechain compress | ✅ `sidechaincompress` | ✅ | ❌ | ✅ |

**Verdict** : ffmpeg for **iteration** (60+ mix variants in a day, each in 30 seconds). Logic Pro for **final mastering** if the project needs spatial / mastering work that ffmpeg can't do. For a short cinépoème with clean stereo, ffmpeg alone is sufficient and far faster.

### Editing

**Why ffmpeg and not Premiere / FCP / Resolve / CapCut** : see the dedicated comparison section below.

**Short answer** : ffmpeg for **iteration in a sprint**. NLE for **finalization** if visual complexity demands it (color grade, masking, morph cuts). In a 24h sprint, ffmpeg wins.

### Subtitles

- **whisper.cpp** (`whisper-cli`) for EN transcription (local, Apple Silicon native, GGUF model).
- Manual or LLM-assisted FR translation preserving SRT timestamps.
- Convert to `.ass` (SubStation Alpha) for styling control.
- Burn via **ffmpeg-full** with libass enabled. Default brew ffmpeg ships **without libass** — silent fail. `brew install ffmpeg-full`.

---

## 6. Slow-motion algorithms compared

When your video timeline runs short and you need to stretch a shot or build a contemplative pacing:

| Algorithm | Quality | Speed | Cost | Notes |
|---|---|---|---|---|
| **setpts (frame duplication)** | Low (jerky on >1.5x) | Fast | Free | Use only for 1.05-1.2x subtle stretches |
| **minterpolate mci** (ffmpeg motion-compensated interp) | Medium | Slow on CPU | Free | Default choice for moderate slowdown 1.4-2x |
| **RIFE** (NCNN GPU) | High | Fast on GPU | Free | Best open-source, requires ncnn or vapoursynth setup |
| **FILM** (Google) | High | Medium | Free | TF model, paper-grade results |
| **Topaz Video AI** | Very high | Slow | $300/year | Commercial, marketing-grade |
| **Twixtor** | Very high | Slow | $300+ | Plugin for AE / Premiere, ground truth for slow-mo |

**For this pipeline** : `minterpolate mci` for moderate slow (1.4-2x), `setpts` for subtle (1.1-1.2x). RIFE for hero shots where you can spend GPU time.

```bash
# minterpolate slow 1.8x with motion-compensated interpolation
ffmpeg -i in.mp4 -vf "setpts=1.8*PTS,minterpolate=fps=30:mi_mode=mci" out.mp4
```

---

## 7. Edit format choice (EDL vs FCPXML vs OTIO)

| Format | Strengths | Use case |
|---|---|---|
| **EDL (CMX 3600)** | Plain text, 50 years of industry adoption, trivial to parse, human-readable, ffmpeg-compatible (via concat demuxer translation) | When your editor agents need to output structured cuts a script can consume. **Used in this repo.** |
| **FCPXML** | Rich metadata, Apple-native, supports markers / effects / multi-track | Handoff to Final Cut Pro for finalization. SpliceKit MCP path. |
| **OTIO (OpenTimelineIO)** | Open standard, multi-NLE bridge (FCP / Resolve / Premiere all read it), Python lib | Multi-NLE interop, future-proofing. |
| **AAF** | Industry standard for high-end | Avid pipelines. Heavy. |

**Why this repo uses EDL-like JSON** : each editor agent outputs a list of `[plan_id, duration, position]` entries that's trivial for the build script to consume. Could be ported to OTIO with one Python pass.

---

## 8. Cost analysis: local vs commercial

### One-time hardware investment (local pipeline)

| Item | Cost |
|---|---|
| M-series Mac (M3/M4 Pro/Max, 36GB+ RAM) | $2500-5000 |
| External 4TB SSD | $300-500 |
| Audio monitoring (headphones) | $200-500 |
| **Total** | **$3000-6000 once** |

### Per-film cost — fully local stack

| Component | Tool | Cost |
|---|---|---|
| Image gen | Flux Schnell / Krea local | $0 (electricity) |
| LoRA training | kohya / OneTrainer local | $0 |
| Image edit | InvokeAI / Gemini Flash local-ish | $0 |
| i2v | LTX 2.3 local (ComfyUI) | $0 |
| Voice clone | XTTSv2 / OpenVoice / Tortoise | $0 (quality below MiniMax) |
| Music | MusicGen local | $0 (quality below Lyria/ElevenLabs) |
| Edit | ffmpeg | $0 |
| Transcribe | whisper.cpp | $0 |
| **Per-film** | | **~$0 + electricity** |

### Per-film cost — fully commercial stack (~10 min film, ~80 shots)

| Component | Tool | Estimate |
|---|---|---|
| Image gen (200 PNGs) | Krea 2 + GPT Image 2 | $15-40 |
| LoRA training (1-2 characters) | Krea 2 LoRA / Flux fal | $5-15 |
| i2v hero (15 shots Seedance 2 Pro 1080p 6s) | Replicate / PiAPI | $12 |
| i2v rushes (65 shots LTX 2.3 fast 720p 5s) | fal / Replicate | $13 |
| Voice clone | Replicate MiniMax | $5 |
| Music (3 tracks) | Lyria / ElevenLabs | $10-20 |
| Storage CDN | fal storage | $0 |
| Transcribe | whisper.cpp local | $0 |
| **Per-film** | | **~$60-110** |

### Hybrid recommendation (this repo's approach)

| Phase | Stack | Rationale |
|---|---|---|
| Moodboard / 100 draft images | Krea 2 cloud | Speed > cost |
| LoRA training | Krea 2 / Flux fal | Avoid local GPU setup |
| i2v rushes (80% of shots) | LTX 2.3 (local if possible, fal otherwise) | Cheap iteration |
| i2v hero (20% of shots) | Seedance 2 Pro via Replicate or PiAPI | Best-in-class quality |
| Voice cloning | MiniMax via Replicate | Stable, $3 + $5 |
| Music | Lyria + ElevenLabs Music | Mix sources |
| Edit / mix / subs | ffmpeg-full local | Free, scriptable |
| **Total per film** | | **~$40-80** |

**60-80% cost savings vs all-commercial**, and you keep the speed of cloud for the moments where speed matters.

---

## 9. Why ffmpeg and not an NLE (extended)

### Option A — ffmpeg only (this pipeline)

**For:**
- No license, scriptable, parallel runs, reproducible (same script = same output assuming deterministic input).
- Runs on Mac mini, no GPU dependency.
- Background tasks: 4 montage builds in parallel impossible in an NLE.

**Against:**
- No timeline visualization → blind composition.
- Slow iteration on shot-duration changes (full re-render).
- No morph cut, no auto-stabilization, no masking, no GPU reverb.
- Subtitle styling requires libass + well-formed ASS.

### Option B — Pilot Final Cut Pro from Claude Code

Via **SpliceKit** (in-process dylib JSON-RPC, in-FCP injection) → MCP exposed.

**For:**
- Native timeline visualization, color grade, masks, morph cuts, audio plugins.
- Native subtitle burn via FCP captions.

**Against:**
- FCP RAM/GPU on the same Mac.
- SpliceKit specific setup, can break on FCP updates.
- Not reproducible (FCP project ≠ script).

### Option C — Pilot DaVinci Resolve from Claude Code

Via official **DaVinciResolveScript Python API**.

**For:**
- Stable documented API.
- Reference color grading (Resolve is the cinema standard).
- Fusion compositing.
- Free tier powerful.

**Against:**
- Heavy GUI, slow boot.
- Python API indirection.

### Option D — Pilot Premiere Pro from Claude Code

Via **Adobe MCP** (5 servers: Photoshop / Premiere / AE / Illustrator / InDesign), UXP scripts.

**For:**
- Pro workflow, AE integration.
- Rich UXP / ExtendScript.

**Against:**
- Adobe subscription.
- UXP API less mature than Resolve / SpliceKit.
- Premiere instability on long projects.

### Option E — CapCut / iMovie / InVideo

- CapCut: UI automation via Playwright on the web app. No serious API.
- iMovie: limited AppleScript, not pro-grade.
- InVideo: SaaS web, Playwright-automatable but free-tier limited.

**Verdict** : useful for high-volume social media templates, not for a cinépoème.

### When to switch from ffmpeg to NLE

- Color grading requires LUT pipeline + 10-bit + look development → **Resolve**.
- Heavy VFX / compositing / motion graphics → **AE via Adobe MCP**.
- Spatial audio / Dolby Atmos → **Logic Pro** or **Pro Tools** (handoff via OMF or AAF).
- Pure speed and reproducibility on a sprint → **ffmpeg**.

---

## 10. Comparison: AI generation platforms (May 2026)

| Platform | Image | i2v | Voice clone | Music | CLI/API | Notes 2026 |
|---|---|---|---|---|---|---|
| **fal.ai** | Flux, etc. | Seedance 2 / LTX 2.3 | MiniMax | Stable Audio | Rich Python SDK | Fragile account lock; storage works even locked |
| **Replicate** | Flux | Seedance 1/2, LTX | MiniMax | Lyria, ACE | Stable API | Pricier but reliable |
| **PiAPI** | — | Seedance 2 | — | — | REST API behind Cloudflare WAF, 2-job concurrent limit | UA ban on python-urllib |
| **Krea** | Krea 2, Flux 2, Z Image, LoRA training | Seedance 2 (UI only) | — | — | MCP exposes Seedance 1; Playwright for v2 | Best web canvas for AI moodboarding |
| **ChatGPT image (GPT Image 2)** | OK, prompt-faithful | — | — | — | OpenAI API | Hero shots, precise composition |
| **Gemini Flash "nano banana"** | Multimodal edit | — | — | — | Google API | Best "Photoshop-light" via API |
| **Higgsfield** | — | i2v with motion control | — | — | API + CLI | Strong on character motion / dance |
| **Hailuo (MiniMax)** | — | i2v / t2v | speech-02-hd | Music v2.6 | API direct or via Replicate | Voice clone reference |
| **Runway Gen-4** | — | i2v / t2v / v2v | — | — | API | v2v reference, expensive |
| **LumaLabs (Dream Machine + Ray 2)** | — | i2v with camera controls | — | — | API | Camera control via prompt is strong |
| **OpenAI Sora (API)** | — | t2v primarily | — | — | Limited API access | High quality but t2v-first |
| **LTX 2.3 (Lightricks)** | — | i2v open-source | — | — | Hugging Face / ComfyUI local | **Default for 80% iteration** |
| **Hunyuan Video (Tencent)** | — | t2v / i2v open | — | — | HF / ComfyUI local | Long-shot capability |
| **Wan Video 2.1 (Alibaba)** | — | i2v open | — | — | HF / ComfyUI local | Strong on hands and faces |
| **CogVideoX** | — | i2v / t2v open | — | — | HF / ComfyUI local | Lightweight |
| **Pika** | — | i2v | — | — | API | Generalist, mid-quality |
| **ElevenLabs** | — | — | Voice clone, SFX, Music v3 | Music v3 | API stable | Best ecosystem for audio |
| **Suno** | — | — | — | Music | API | Best song generation if you need vocals |
| **MusicGen / AudioCraft (Meta)** | — | — | — | Music | HF local | Free local music |

**Practical recommendation** : never depend on a single provider. The pipeline this repo describes runs on **fal (storage) + Replicate (generation + voice clone) + Krea 2 (moodboard) + LTX 2.3 (rushes i2v) + Seedance 2 Pro (hero shots) + ElevenLabs (music + SFX) + whisper.cpp (transcribe) + ffmpeg-full (edit)**.

---

## 11. Worldbuilding asset taxonomy (what you generate before you cut)

The asset library a film needs **before editing can start** :

```
project/
├── script.md                           # the text (from Claude Project)
├── palette.md                          # 3-5 dominant + 1-2 accent colors
├── characters/
│   └── <name>/
│       ├── sheet_front.png             # character sheet, 5-10 angles
│       ├── sheet_3q.png
│       ├── sheet_profile.png
│       ├── sheet_back.png
│       ├── sheet_close.png
│       ├── sheet_full.png
│       ├── sheet_expressive_*.png
│       └── lora.safetensors            # optional LoRA for stable identity
├── locations/
│   └── <name>/
│       ├── view_wide.png               # establishing
│       ├── view_medium.png
│       ├── view_close.png
│       ├── view_night.png
│       └── view_dawn.png
├── props/
│   └── <name>.png                      # reference for each key object
├── storyboard.md                       # vignettes + captions per beat
├── storyboard/
│   └── beat_001_v1.png                 # vignette images, 1-3 per beat
├── pool/                               # final-grade source images for i2v
│   └── beat_001_v*.png                 # 3-5 alternatives per vignette
├── rushes/                             # i2v outputs
│   └── beat_001.mp4
├── audit.md                            # FIDELE/BUG/DOUBLON tagging
├── pool_validated/
├── pool_quarantine/
├── voice/
│   ├── sample_clean.wav                # 75s clean sample for clone
│   ├── vo.mp3                          # generated VO
│   └── vo_segments/                    # per-segment cuts if needed
├── music/
│   ├── drone.wav
│   ├── accents.mp3
│   └── club.mp3
├── edl/
│   ├── murch.md                        # editor #1
│   ├── marker.md                       # editor #2
│   ├── schoonmaker.md                  # editor #3
│   ├── pagh_andersen.md                # editor #4
│   └── baxter.md                       # editor #5
├── subs/
│   ├── vo.srt                          # whisper.cpp EN
│   └── vo_fr.srt                       # translated FR
├── builds/
│   ├── V0.1_murch.mp4
│   ├── V0.2_marker.mp4
│   └── V1.0_final.mp4
└── delivery/
    ├── master_h264.mp4
    └── email_draft.md
```

Every step has a deliverable. Every deliverable has a place. The orchestrator agent reads and writes through this tree.

---

## 12. Edit grammar: teaching the agent YOUR signature

Generic editor personas (Murch, Marker, etc.) give you a generic cinema grammar. They don't give you **your** grammar. The cheap workaround during a sprint: invoke them as "council" personas for diverse perspectives, then have the director agent synthesize.

The deeper solution: **feed your past films to a vision model and extract your signature**.

This repo includes (or will include) `ISMAEL_EDIT_GRAMMAR.md` — a synthesis of 4 of the filmmaker's films (Maalbeek, Swatted, Ondes Noires, Rewild) analyzed via **Gemini 2.x/3.x Pro** multimodal video input. The output:

- Average shot duration per film and across the body of work
- Cut types and their distribution
- Image-sound offset patterns
- Refused effects (what this filmmaker NEVER does)
- Held-long shots (what they hold for 20+ seconds and why)
- Visual motifs and recurring framings
- Color tendencies
- Closing shot patterns

This document then becomes a **bible** injected into Claude Code via `CLAUDE.md` (project-level) or a custom skill. Every future film the agent helps build will follow this grammar by default, with the filmmaker overriding case-by-case.

**This is the meta-method** : the agent doesn't learn your grammar by chatting with you. It learns by being shown your prior body of work.

> If you don't have a body of work yet — borrow. Pick 3-5 filmmakers whose grammar you admire, feed Gemini, extract, blend, override. The agent will produce in that blended grammar until you have your own films to feed it.

---

## 13. Voice cloning > TTS (extended)

Every generic TTS tested (ElevenLabs v3 with `[breath]` `[tearful]` tags, calm voices Sarah / Matilda / River / Charlotte / Bianca / Alice) sounded **"highschool drama"**. The voice failed to carry the text — the ear disengaged.

Voice cloning of a cinema-grade voice on 75s of clean sample = category shift. The clone reproduces what TTS cannot: breath, vocal tell, grain, prosody.

**Three hard lessons** :
- **Clean sample mandatory**. A sample where the target speaks alongside another voice contaminates the clone (the clone drifts toward a mixed/masculinized average). Always isolate a monophonic extract from a moment where only the target speaks.
- **One single clone for the whole film** beats four mood-matched clones. Mood shifts come from `speed` parameter + natural prosody, not from a vocal mosaic.
- **Replicate `minimax/voice-cloning` → `minimax/speech-02-hd`** : quality leader as of May 2026. ~$3 clone + $0.05/1k chars. Alternative: fal `MiniMax`, equivalent quality.

---

## 14. Technical fails (cataloged)

### fal.ai: locked account despite positive balance
Top-up applied → lock flag not cleared infra-side. Storage keeps working but generation blocked. Single-provider dependency is fragile.

### PiAPI: User-Agent ban + 2-concurrent-jobs limit
- `Python-urllib` User-Agent → systematic HTTP 403 (Cloudflare WAF). Patch: header `User-Agent: Mozilla/5.0...`.
- Basic plan hard-caps **2 active tasks**. Launcher must submit-wait-submit. For 17 shots × 2-3 min: ~40 min queue.
- Zombie pending tasks block slots; use DELETE endpoint to cancel.

### Krea exposes Seedance via UI but not via MCP
Official Krea MCP exposes only Seedance 1.0. v2.0 only via web UI → only usable from Claude Code via **Playwright / Browser Use** automation, not direct CLI.

### Video looping = perceived false repetitions
Looping (`-stream_loop -1`) to match VO duration → the viewer sees first shots reappear = perceived as broken intentional repetitions. **Don't loop. Slow more. Add material.**

### Prompt ↔ image mapping mismatch
Quick batch identification of PNG timestamps → similar frames confused → wrong prompt applied to wrong image → AI hallucination on top of mismatch. **Visual audit (extract frame + read with vision agent + tag) is mandatory** before integration.

### libass missing from default brew ffmpeg
`brew install ffmpeg` (8.x) ships **without libass** → `subtitles=*.srt` filter returns `No option name near`. Install `ffmpeg-full` for libass support. Misleading: ffmpeg works for everything except subtitle burning.

### Whisperx → transformers import error
`whisperx` breaks on `Wav2Vec2ForCTC` import when transformers updates. Fallback: **whisper.cpp** via `whisper-cli` (Apple Silicon native, GGUF model).

### Cloudflare 1010 ban
Cloudflare-protected APIs (PiAPI, some others) ban request signatures lacking browser User-Agent. Always set realistic browser UA when scripting outbound HTTP from Python.

### Default audio mix truncation (-shortest)
`ffmpeg -shortest` truncates audio to the shorter video — silent kill of the VO when video < audio. Solution: drop `-shortest`, use `-t <vo_duration>`, or extend video via slowdown / extra material.

### Slow factor poorly calibrated
First pass: 1.4x slow → 4-5min video for 9:53 VO → 4+ min frozen frame at end. Hard lesson: pre-compute total pool natural duration, derive needed slow factor, validate before encoding.

---

## 15. Technical wins (cataloged)

- **Parallel background tasks**: 4 montage builds + PiAPI generation + 5 editor agents simultaneously. The CLI's `run_in_background` flag is the unique enabler.
- **Sub-agents for visual analysis**: an `audit` sub-agent extracts frames from 50+ rushes, reads with vision, writes tagged MD in 6 min. ~30 min saved per audit cycle.
- **Single-pass 4-layer audio mix**: `ffmpeg -i vo -i drone -i accents -i club -filter_complex "amix=inputs=4..."` in one process.
- **Inter-provider pivot without loss**: storage CDN on fal (free, doesn't lock with generation account) + generation on independent provider → URLs portable across services.
- **Email + Drive from CLI**: `gws drive +upload` + `mail-cli` → public link + email sent in two commands.
- **Whisper.cpp Apple Silicon native**: faster than Python whisper-x, no Python dependency hell, ggml-small.bin = 488MB and acceptable quality for VO transcription.

---

## 16. Artistic wins

- **Editor council surfaces structural disagreements** that are the film's subject (Schoonmaker values the neon aquarium as oneiric; Pagh Andersen bans it as a capitalist mirage). The disagreement becomes editing material.
- **Voice-cloning a signature timbre** shifts the work from amateur to programmable-by-committee.
- **Moderate slow 1.5-1.8x** on contemplative shots = subtle oneiric signature, not "advertising slow-mo".
- **Burned FR subs** transform a bilingual/anglophone object into French-receivable form for francophone programming.
- **The 24h constraint** as a creative driver (no time for second-guessing, more time for instinct) — but watch out for the cognitive tunnel (see limits below).

---

## 17. Honest limits of this method

A method note is dishonest if it sells the dream. The hard limits :

- **60% of the value came from method, 40% from crisis management.** This repo documents both but if you treat crisis management as method, you'll fail to replicate.
- **Bugs delivered unseen**. The 24h sprint forces shipping objects you haven't fully validated. The pipeline can produce a final MP4 with a hallucinated smartphone in 2095 that no one caught. Plan for a post-delivery review cycle, don't pretend the final-on-deadline is the final-final.
- **Editor council = intellectual prosthesis, not a real decision mechanism**. In the heat of a sprint, you'll dismiss the editor whose grammar diverges most from yours ("he's nuts, don't listen"). The council legitimates your existing intuitions more than it challenges them. To use it as a real challenger, you'd need to honor the dissenting EDL even when it hurts.
- **No cognitive breaks during a 24h sprint = tunnel effect**. You make process decisions, not creative decisions. The creative decisions were made before (during the 48h text), or get made post-hoc (during the next project's reflection). A 24h sprint is execution, not creation. Don't confuse them.
- **AI non-determinism**. The pipeline's "reproducibility" is partial — same script, same prompts, same seeds where applicable, but i2v models drift between runs. The exact same film can't be made twice. Plan for variance, not reproducibility.
- **Single-provider single-point-of-failure**. The session almost died when fal locked the account mid-production. Always have a backup provider warmed up before you need it.
- **CLI envelope cost**. Multi-hour Claude Code sessions consume tokens. Sonnet flow + Opus council = several dollars per session. The "$60-110 per film" cost estimate doesn't include the Claude tokens (~$20-50 for a 24h session). Factor it in.

---

## 18. Lessons learned (consolidated)

1. **Two-mind writer split** (Head + Arms in two Claude Project windows) > one window doing both.
2. **CLI Claude is your studio**, not your writer. Keep the text inviolate in the Project.
3. **Voice cloning > TTS** for any narrative project. Not optional.
4. **Storage CDN separate from generation account** = resilience.
5. **80/20 model strategy**: cheap+fast for 80% iteration, premium for 20% final.
6. **Sub-agents > monolithic prompts** for specialized tasks.
7. **Parallel background tasks** for anything that runs while you think.
8. **Audit before integrate** — every generated asset gets visually validated.
9. **Don't loop video** — slow modestly or generate more.
10. **ffmpeg to iterate fast, NLE to finalize** if needed.
11. **Show every email draft before sending** — the CLI sends instantly, that's why human checkpoint matters.
12. **Feed past films to a vision model** to extract your grammar. The agent should learn from your work, not from your chats.
13. **Cost local vs commercial**: hybrid wins. Local for iteration, commercial for hero moments.
14. **Honor the deadline as a constraint, not as the law**. A film delivered with bugs is worse than a film delivered tomorrow.

---

## 19. Tools summary (May 2026)

**CLI / dev** : Claude Code (Anthropic), `gh`, `gws`, `mail-cli` (custom), `gdrive`, `rclone`, `whisper-cli` (whisper.cpp), `ffmpeg`, `ffmpeg-full` (libass), `gemini` CLI, `python3`, `curl`, `playwright`.

**AI platforms** : fal.ai (storage + i2v + clone, fragile), Replicate (i2v + clone + music, reliable), PiAPI (Seedance 2 i2v, Cloudflare-protected), Krea 2 (moodboard + LoRA, web-first), ChatGPT (image), Gemini (image edit + video analysis), ElevenLabs (TTS + music + SFX), MiniMax (voice clone via Replicate or fal), LumaLabs (i2v alt), Higgsfield (motion-controlled i2v), Runway (v2v).

**Models (May 2026)** : Seedance 2.0 Pro / Fast (ByteDance i2v), LTX 2.3 (Lightricks open i2v), Hunyuan Video (Tencent open), Wan Video 2.1 (Alibaba open), Flux 2 / Z Image (open image gen + LoRA), GPT Image 2 (OpenAI), Krea 2 (Krea native), MiniMax `speech-02-hd` (voice clone), Lyria 2 (music), ElevenLabs Music v3, Whisper small (transcribe), Gemini 2.5 / 3.x Pro (multimodal analysis).

**Notable MCPs** : Adobe (Photoshop / Premiere / AE / Illustrator / InDesign), SpliceKit (FCP), Blender, Playwright, Pinecone, clipboard-vision, ComfyUI, Krea, Beeper, Postiz.

**Sub-agent personas (in Claude Code)** : Director, Worldbuilder, Storyboard, Asset Manager, Generation Director, Editor Council (5 personas), Audio Engineer, Subtitle Engineer, Audit, Delivery, Cost Tracker.

---

## 20. Coda

This isn't a turnkey kit. Every film has its own pipeline. The takeaway: **piloting a complete production chain from Claude Code is feasible and fluid for a filmmaker who knows what they want**, provided you accept three trade-offs:

- Slower fine-tuning iteration than an NLE.
- No native timeline visualization during ffmpeg editing.
- Dependency on fragile external platforms (locks, rate limits, API changes, model rotations).

The gain: **reproducibility, parallelism, traceability**, and most of all — **staying in one mental environment** for the duration of a sprint, without context-switching between 6 applications. The filmmaker stays in the head where the film lives.

The deeper bet: **the agent team will become your studio**. Worldbuilder, Storyboard, Generation Director, Editor Council, Audio Engineer — each one a specialist agent that learns your grammar over multiple projects. The next sprint will be 18h instead of 24h. The one after that 12h. The text (the only thing that can't be automated) keeps its 48h.

What gets delegated, what stays yours, becomes the next political question of filmmaking.

---

*See also : [`ISMAEL_EDIT_GRAMMAR.md`](./ISMAEL_EDIT_GRAMMAR.md) (work in progress, extracted from Maalbeek / Swatted / Ondes Noires / Rewild via Gemini multimodal). [`scripts/`](./scripts) for runnable bits.*

*Notes taken the day after a ~24h sprint; expanded subsequently on cooler reflection.*
