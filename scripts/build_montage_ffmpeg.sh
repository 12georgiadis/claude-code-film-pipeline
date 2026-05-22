#!/bin/bash
# Generic ffmpeg montage builder pattern used for the cinépoème.
#
# Pipeline:
# 1. Normalize each clip to 1920x1080 30fps, optional slowdown via setpts
# 2. Concat via demuxer (HARD CUTS only, no crossfades)
# 3. Build 4-layer audio mix (VO + drone + accents + club)
# 4. Mux video + audio, optional burn subtitles via libass
#
# Requires: ffmpeg-full (with libass) for subtitle burning
#   brew install ffmpeg-full
#
# Plain ffmpeg from brew core does NOT have libass — subtitles filter fails
# with "No option name near 'subs.srt'".
set -e

FFMPEG=/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffmpeg
POOL="${POOL_DIR:-./pool}"
OUT="${OUT_DIR:-./output}"
VO="${VO_FILE:-./vo.mp3}"
SRT="${SRT_FILE:-./subs.srt}"
MUSIC_DRONE="${MUSIC_DRONE:-./drone.wav}"
MUSIC_ACCENTS="${MUSIC_ACCENTS:-./accents.mp3}"
MUSIC_CLUB="${MUSIC_CLUB:-./club.mp3}"
mkdir -p "$OUT"

TMP=$(mktemp -d)
echo "[+] TMP=$TMP"

# Plans signature with heavy slowdown (lyrical scenes)
SLOW_HEAVY="CLIP_CLIMAX CLIP_SIGNATURE_END"
is_heavy() { echo "$SLOW_HEAVY" | grep -qw "$1"; }

# List of clips in narrative order — fill with your IDs
PLANS=(
  CLIP_OPEN_1 CLIP_OPEN_2
  CLIP_INTIME_1 CLIP_INTIME_2 CLIP_INTIME_3
  CLIP_LYRICAL_1 CLIP_LYRICAL_2
  CLIP_CLIMAX
  CLIP_EPILOGUE_1
  CLIP_SIGNATURE_END
)

# Normalize each clip (slowdown modéré 1.8x default, heavy 2.5x for signature)
i=0
for p in "${PLANS[@]}"; do
  src="$POOL/${p}.mp4"
  [ ! -f "$src" ] && { echo "  [SKIP] $p"; continue; }
  out="$TMP/$(printf "%03d" $i)_${p}.mp4"
  if is_heavy "$p"; then FACTOR=2.5; else FACTOR=1.8; fi
  $FFMPEG -loglevel error -i "$src" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,setpts=${FACTOR}*PTS,fps=30" \
    -c:v libx264 -preset veryfast -crf 18 -an "$out"
  echo "  [SLOW ${FACTOR}x] $p"
  i=$((i + 1))
done

# Concat — hard cuts only via demuxer
ls "$TMP"/[0-9]*.mp4 | sort | awk '{print "file '\''" $0 "'\''"}' > "$TMP/list.txt"
$FFMPEG -loglevel error -f concat -safe 0 -i "$TMP/list.txt" \
  -c:v libx264 -preset veryfast -crf 18 -an "$TMP/video.mp4"

VIDDUR=$($FFMPEG -i "$TMP/video.mp4" 2>&1 | grep Duration | awk '{print $2}' | tr -d ',' | awk -F: '{print ($1*3600)+($2*60)+$3}')
echo "[+] video duration: ${VIDDUR}s"

# Audio: VO at 0dB, drone at -28dB, accents at -30dB, club at -24dB (only on spectacle segment)
$FFMPEG -loglevel error -stream_loop -1 -i "$MUSIC_DRONE" -t "$VIDDUR" -af "volume=-28dB" -ac 2 "$TMP/drone.wav"
$FFMPEG -loglevel error -i "$VO" -af "volume=0dB,apad=pad_dur=20" -ac 2 "$TMP/vo.wav"
$FFMPEG -loglevel error -stream_loop -1 -i "$MUSIC_ACCENTS" -t "$VIDDUR" -af "volume=-30dB" -ac 2 "$TMP/accents.wav"
$FFMPEG -loglevel error -i "$MUSIC_CLUB" -af "adelay=215000|215000,volume=-24dB,apad=pad_dur=300" -t "$VIDDUR" -ac 2 "$TMP/club.wav"

# Mix all 4 layers in a single pass
$FFMPEG -loglevel error -i "$TMP/vo.wav" -i "$TMP/drone.wav" -i "$TMP/accents.wav" -i "$TMP/club.wav" \
  -filter_complex "[0][1][2][3]amix=inputs=4:duration=longest:normalize=0[a]" \
  -map "[a]" -c:a aac -b:a 192k "$TMP/audio.m4a"

# Pass 1: mux video + audio (audio drives the total duration)
$FFMPEG -loglevel error -i "$TMP/video.mp4" -i "$TMP/audio.m4a" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k "$TMP/inter.mp4"

# Pass 2: burn subtitles (requires libass-enabled ffmpeg)
OUTFINAL="$OUT/montage_$(date +%H%M).mp4"
$FFMPEG -loglevel error -y -i "$TMP/inter.mp4" \
  -vf "subtitles=${SRT}" \
  -c:v libx264 -preset veryfast -crf 20 -c:a copy "$OUTFINAL"

echo "[OK] $OUTFINAL"
rm -rf "$TMP"
