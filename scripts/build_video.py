#!/usr/bin/env python3
"""
scripts/build_video.py — Automated High-Quality Video Demonstration Builder

Generates:
1. submission-assets/excursionlens_demo.srt (Captions)
2. submission-assets/excursionlens_demo.mp4 (1920x1080, 30fps H.264, burned-in subtitles, normalized voiceover + soft ambient bed)
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "docs" / "assets"
OUT_DIR = ROOT / "submission-assets"
AUDIO_DIR = OUT_DIR / "audio"

SCENES = [
    {
        "id": 1,
        "image": ASSETS_DIR / "screenshots" / "01_case_overview.png",
        "audio": AUDIO_DIR / "scene1.mp3",
        "text": [
            ("00:00:00,000", "00:00:06,000", "Every year, cold-chain excursions compromise critical biopharmaceuticals during transit."),
            ("00:00:06,000", "00:00:13,000", "In regulated life sciences, an unconstrained AI that hallucinates approval risks patient safety."),
            ("00:00:13,000", "00:00:20,500", "This is ExcursionLens: an evidence-driven forensic system architected for NVIDIA Nemotron."),
            ("00:00:20,500", "00:00:28,000", "Notice our header: this public demonstration uses transparent deterministic fixture replay."),
            ("00:00:28,000", "00:00:36,400", "Live Nebius Token Factory execution is not being claimed in this recording. The system operates fail-closed.")
        ]
    },
    {
        "id": 2,
        "image": ASSETS_DIR / "screenshots" / "02_timeline_evidence.png",
        "audio": AUDIO_DIR / "scene2.mp3",
        "text": [
            ("00:00:36,400", "00:00:43,000", "Our foundation is 100% deterministic code. Zero generative tokens are used for physics."),
            ("00:00:43,000", "00:00:50,500", "For shipment NMB-204, Python analyzes raw IoT telemetry, detecting a 40-minute breach above 8°C."),
            ("00:00:50,500", "00:00:57,500", "Peak temperature reaches 10.5°C with an Area Under the Curve of 50.5 degree-minutes."),
            ("00:00:57,500", "00:01:04,500", "Aligned with custody logs, the breach correlates with open bay doors at Newburgh Hub at 10:18 UTC.")
        ]
    },
    {
        "id": 3,
        "image": ASSETS_DIR / "architecture.png",
        "audio": AUDIO_DIR / "scene3.mp3",
        "text": [
            ("00:01:04,500", "00:01:12,000", "Clicking 'Investigate Excursion' triggers our bounded state-machine pipeline."),
            ("00:01:12,000", "00:01:19,500", "The system steps through schema validation, normalization, and regulatory guidance matching."),
            ("00:01:19,500", "00:01:27,500", "In this fixture demonstration, pre-vetted CDC and WHO summaries establish allowable thresholds.")
        ]
    },
    {
        "id": 4,
        "image": ASSETS_DIR / "screenshots" / "03_hypothesis_board.png",
        "audio": AUDIO_DIR / "scene4.mp3",
        "text": [
            ("00:01:27,500", "00:01:34,500", "Next, the pipeline executes our dual-pass causal engine, structured for NVIDIA Nemotron-70B."),
            ("00:01:34,500", "00:01:42,000", "Generator synthesis produces three competing hypotheses, followed by an adversarial skeptic pass."),
            ("00:01:42,000", "00:01:50,000", "While a naive model might blame refrigeration failure, the skeptic sees vehicle alternator bus at 12.8V."),
            ("00:01:50,000", "00:01:58,000", "This directly falsifies compressor power loss. Prohibited overclaims are trapped by validators.")
        ]
    },
    {
        "id": 5,
        "image": ASSETS_DIR / "screenshots" / "04_counterfactual.png",
        "audio": AUDIO_DIR / "scene5.mp3",
        "text": [
            ("00:01:58,000", "00:02:05,000", "To assist quality engineers with corrective actions, our Counterfactual Workbench simulates interventions."),
            ("00:02:05,000", "00:02:12,000", "Enforcing a 5-minute door closure threshold eliminates the excursion completely in simulation."),
            ("00:02:12,000", "00:02:18,000", "Simulated breach duration is reduced from 40.0 minutes to zero, proving corrective SLA efficacy.")
        ]
    },
    {
        "id": 6,
        "image": ASSETS_DIR / "screenshots" / "05_review_packet.png",
        "audio": AUDIO_DIR / "scene6.mp3",
        "text": [
            ("00:02:18,000", "00:02:26,000", "Finally, ExcursionLens generates an auditable Quality Review Packet with observation digests and model receipts."),
            ("00:02:26,000", "00:02:33,000", "The product remains strictly quarantined until an authorized quality professional signs off."),
            ("00:02:33,000", "00:02:39,600", "ExcursionLens bridges physical telemetry, regulatory guidance, and adversarial reasoning into an auditable science.")
        ]
    }
]


def write_srt(out_srt: Path):
    idx = 1
    lines = []
    for sc in SCENES:
        for start, end, text in sc["text"]:
            lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
            idx += 1
    out_srt.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Written captions: {out_srt.name} ({idx-1} cues)")


def get_duration(p: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_srt = OUT_DIR / "excursionlens_demo.srt"
    write_srt(out_srt)

    # 1. Measure audio durations
    durations = [get_duration(sc["audio"]) for sc in SCENES]
    total_audio_sec = sum(durations)
    print(f"Total audio duration: {total_audio_sec:.2f}s ({int(total_audio_sec // 60)}m {int(total_audio_sec % 60)}s)")

    # 2. Concat all narration audio
    concat_list = OUT_DIR / "audio_concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for sc in SCENES:
            f.write(f"file '{sc['audio'].resolve().as_posix()}'\n")

    merged_voice = OUT_DIR / "voice_merged.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "pcm_s16le", str(merged_voice)], check=True)

    # 3. Generate soft ambient tone bed at -24 dB
    ambient_bed = OUT_DIR / "ambient_bed.wav"
    # Generate harmonic ambient chord (A minor / calm scientific pad: 220Hz, 261.6Hz, 329.6Hz) at very low volume
    synth_filter = (
        f"aevalsrc='0.03*sin(2*PI*220*t) + 0.02*sin(2*PI*261.63*t) + 0.02*sin(2*PI*329.63*t)':d={total_audio_sec:.2f}:s=44100"
    )
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", synth_filter, "-af", "volume=0.08,afade=t=in:ss=0:d=3,afade=t=out:st=" + f"{total_audio_sec-3:.2f}:d=3", str(ambient_bed)], check=True)

    # 4. Mix voiceover + ambient bed
    mixed_audio = OUT_DIR / "audio_final.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(merged_voice), "-i", str(ambient_bed), "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.15[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2", str(mixed_audio)], check=True)

    # 5. Build scene video segments (1920x1080 30fps)
    segment_files = []
    for sc, dur in zip(SCENES, durations):
        seg_p = OUT_DIR / f"segment_{sc['id']}.mp4"
        segment_files.append(seg_p)
        img_p = sc["image"]
        # Scale & pad to 1920x1080, subtle slow zoom or clean freeze
        vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#17201E,format=yuv420p"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_p),
            "-t", f"{dur:.2f}",
            "-vf", vf,
            "-r", "30",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            str(seg_p)
        ]
        subprocess.run(cmd, check=True)

    # 6. Concat video segments
    v_concat_list = OUT_DIR / "video_concat.txt"
    with open(v_concat_list, "w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg.resolve().as_posix()}'\n")

    raw_video = OUT_DIR / "raw_video.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(v_concat_list), "-c", "copy", str(raw_video)], check=True)

    # 7. Merge final video + audio + burn subtitles
    final_mp4 = OUT_DIR / "excursionlens_demo.mp4"
    # Format subtitle path for ffmpeg subtitles filter (escape colons and backslashes)
    srt_escaped = str(out_srt.resolve().as_posix()).replace(":", "\\:")
    sub_filter = f"subtitles='{srt_escaped}':force_style='Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H0017201E,BackColour=&H80000000,BorderStyle=4,MarginV=35,Alignment=2'"

    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-i", str(mixed_audio),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_mp4)
    ]
    print("Rendering final video with burned-in subtitles...")
    subprocess.run(cmd_final, check=True)

    final_dur = get_duration(final_mp4)
    print(f"\n🎉 Successfully rendered: {final_mp4}")
    print(f"   Duration: {final_dur:.2f}s ({int(final_dur // 60)}m {int(final_dur % 60)}s)")
    print(f"   Size: {final_mp4.stat().st_size / (1024*1024):.2f} MB")
    print(f"   SRT: {out_srt}")


if __name__ == "__main__":
    main()

