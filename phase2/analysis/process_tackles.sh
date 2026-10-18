#!/usr/bin/env bash
# process_tackles.sh — frame-exact 1080p clip -> HybrIK demo -> track check -> offset record.
# usage : bash phase2/analysis/process_tackles.sh <date> <tackles.txt>
# input : lines "<stem> <start_sec> <end_sec> <tag>" (lines starting with # are skipped)
# output: outputs/<date>/<stem>_<tag>/{<stem>_<tag>_1080p.mp4, hybrik/res.pk, offset.txt, hybrik_track.txt}
# env   : run in the `hybrik` conda env (ffmpeg + torch 1.9.1 live there), cwd = repo root.
set -euo pipefail          # stop at the first failing command / unset variable

DATE="$1"; LIST="$2"
REPO="$HOME/rugby-video-analytics"
HYBRIK="$HOME/HybrIK"
FPS_NUM=60000; FPS_DEN=1001

while read -r stem start end tag; do
  [[ -z "$stem" || "$stem" == \#* ]] && continue
  video=$(ls "$REPO"/data/raw/*/"$stem".MOV | head -1)
  outdir="$REPO/outputs/$DATE/${stem}_${tag}"
  mkdir -p "$outdir"
  clip="$outdir/${stem}_${tag}_1080p.mp4"
  echo "=== [$stem $tag] $(date) video=$video"

  # 1) seconds -> 0-based frame indices: a0 = floor(start*fps), b0 = floor(end*fps)
  a0=$(python -c "print(int($start * $FPS_NUM / $FPS_DEN))" < /dev/null)
  b0=$(python -c "print(int($end * $FPS_NUM / $FPS_DEN))" < /dev/null)
  n_expected=$(( b0 - a0 + 1 ))
  echo "    frames a0=$a0 b0=$b0 n_expected=$n_expected"

  # 2) frame-exact cut + exact 2x downscale; no -ss so that n counts from the file start
  ffmpeg -nostdin -y -hide_banner -loglevel error -i "$video" \
    -vf "select='between(n,${a0},${b0})',setpts=N/FRAME_RATE/TB,scale=1920:1080" \
    -an -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p "$clip"
  n_clip=$(ffprobe -v error -count_frames -select_streams v:0 \
    -show_entries stream=nb_read_frames -of csv=p=0 "$clip" < /dev/null | grep -m1 -E '^[0-9]+$')
  if [[ "$n_clip" != "$n_expected" ]]; then
    echo "ERROR [$stem $tag]: clip has $n_clip frames, expected $n_expected" >&2
    exit 1
  fi
  echo "    clip ok: $clip ($n_clip frames)"

  # 3) offset record (key=value) mapping clip indices back to the original video
  cat > "$outdir/offset.txt" <<EOF
stem=$stem
tag=$tag
start_sec=$start
end_sec=$end
fps=$FPS_NUM/$FPS_DEN
first_orig_0based=$a0
last_orig_0based=$b0
n_frames_expected=$n_expected
n_frames_ffprobe=$n_clip
# clip index i (0-based, order of res['img_path']) -> original 1-based frame = i + 1 + first_orig_0based
EOF

  # 4) HybrIK demo: cwd must be $HYBRIK (relative config/weight paths); stdin detached from $LIST
  hyb_rel=$(realpath -m --relative-to="$HYBRIK" "$outdir/hybrik")   # demo prefixes out-dir with "./" -> must be relative to $HYBRIK
  ( cd "$HYBRIK" && python scripts/demo_video.py --video-name "$clip" --out-dir "$hyb_rel" \
      --save-pk < /dev/null )

  # 5) track check (frame count, bbox jumps / identity switches)
  python "$REPO/phase2/analysis/hybrik_track_check.py" "$outdir/hybrik/res.pk" \
    > "$outdir/hybrik_track.txt" < /dev/null
  cat "$outdir/hybrik_track.txt"

  echo "=== [$stem $tag] done $(date)"
done < "$LIST"