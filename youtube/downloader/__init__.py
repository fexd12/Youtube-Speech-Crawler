import json
import os
import subprocess
from pathlib import Path
from shutil import move

from django.utils.text import slugify
from pydub import AudioSegment

from youtube_wrapper import YouTube
# from pytube import YouTube
from youtube.closed_caption import YouTubeClosedCaption, TranscriptsDisabled

AUDIO_CODEC = "pcm_s16le"
AUDIO_BITRATE = 22050
AUDIO_CHANNEL = 1


def get_youtube_stream(jsonfile, data_dir, closed_caption=None, verbose=True):
    if closed_caption is None:
        closed_caption = ['br', ]
    module = 'youtube-downloader'

    def get_target_path(channel_dir, video):
        target_dir = os.path.join(channel_dir, video['id'])
        Path(target_dir).mkdir(parents=True, exist_ok=False)
        return target_dir

    def extract_segments(channel_dir, video, wav_file, transcript, verbose=verbose):
        if verbose:
            print(f'[{module}] Segment Extraction')
        target_dir = get_target_path(channel_dir, video)
        wav_audio = AudioSegment.from_wav(wav_file)
        for key, value in transcript.items():
            start = value["start"] * 1000
            end = start + (value["duration"] * 1000)
            if verbose:
                print(f'[{module}] > {key}.wav - {start} - {end}')
            seg = wav_audio[start:end]
            seg.export(
                open(os.path.join(target_dir, f'{video["id"]}-{key}.wav'), "wb"),
                format="wav",
                # codec=AUDIO_CODEC,
                # bitrate=str(AUDIO_BITRATE_,
                # parameters=["-ac", str(AUDIO_CHANNEL)]
            )

    def get_caption(channel_dir, video, verbose=verbose):
        if verbose:
            print(f'[{module}] extract closed caption')
        target_dir = get_target_path(channel_dir, video)
        try:
            transcript = YouTubeClosedCaption.get_transcript(video['id'], languages=closed_caption)
            transcript = {
                f'seg_{f"%.{len(str(len(transcript)))}d" % index}': value for index, value in enumerate(transcript)
            }
            json.dump(
                transcript,
                open(os.path.join(target_dir, 'cc.json'), 'w', encoding='utf-8'),
                sort_keys=True, indent=2, ensure_ascii=False
            )
        except TranscriptsDisabled as e:
            print(e)
            return False, None
        return True, transcript

    def m4a_to_wav(m4a, codec=AUDIO_CODEC, bitrate=AUDIO_BITRATE, channels=AUDIO_CHANNEL, verbose=False):
        if verbose:
            print(f'[{module}] convert m4a to wav')
        wav_file = m4a.replace('.m4a', f'-{codec}-{bitrate}-{channels}CH.wav')
        subprocess.call([
            "ffmpeg", "-y", "-i", m4a, "-acodec", codec, "-ar", str(bitrate), "-ac", str(channels), wav_file,
            "-loglevel", "error", "-hide_banner", "-nostats"
        ])

        return wav_file

    def mp4_to_m4a(channel_dir, video, verbose=False):
        video_id = video.get('id')
        if verbose:
            print(f'[{module}] convert mp4 to m4a')
        target_dir = get_target_path(channel_dir, video)
        mp4 = os.path.join(channel_dir, f'{video_id}.mp4')
        m4a = os.path.join(target_dir, f'{video_id}.m4a')
        if not (os.path.exists(mp4) and os.path.exists(m4a)):
            move(mp4, m4a)
        return m4a

    def stream_to_mp4(video, verbose=False):
        video_id = video.get('id')
        try:
            youtube = YouTube(video.get('link', None))
            if verbose:
                print(f'[{module}] download: {video_id} - {youtube.title}')
            stream = youtube.streams.filter(only_audio=True, audio_codec="mp4a.40.2").first()
            stream.download(channel_dir, filename=f"{video_id}")
            return True
        except Exception as e:
            print('error',e)
            return False

    meta = json.load(open(jsonfile, 'r', encoding='utf-8'))
    channel_dir = os.path.join(data_dir, slugify(meta['name']))
    Path(channel_dir).mkdir(parents=True, exist_ok=True)
    for index, video in enumerate(meta['videos']):
        if not stream_to_mp4(video, verbose=verbose):
            continue
        wav_file = m4a_to_wav(mp4_to_m4a(channel_dir, video, verbose=verbose), verbose=verbose)
        has_caption, transcript = get_caption(channel_dir, video, verbose=verbose)
        if has_caption:
            meta['videos'][index]['closed_caption'] = True
            json.dump(meta, open(jsonfile, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            extract_segments(channel_dir, video, wav_file, transcript, verbose=verbose)

    if verbose:
        print(f'[{module}] remove all temporary mp4 files')
    subprocess.call(["rm", f"{channel_dir}/*.mp4"])
