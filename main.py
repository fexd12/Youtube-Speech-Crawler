import json
import os
from pathlib import Path

from django.utils.text import slugify

from youtube.data_api import YoutubeDataAPI
from youtube.data_api import constants
from youtube.downloader import get_youtube_stream

BASE_DIR = os.path.dirname(os.path.abspath('__file__'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MAX_RETRIES = 5


def search_youtube_video_by_query(query, channel=None, language='th', limit=9999, verbose=True):
    module = 'youtube-crawler'

    def _compute_query_metadata(search_videos, verbose=verbose):
        if verbose:
            print(f'[{module}] Creating meta.json')
        channels = {video['channel']['id']: video['channel'] for video in search_videos}
        if verbose:
            print(f'[{module}] channels found: {len(channels)}')
        for channel, data in channels.items():
            channel_name = data.get('name')
            data['videos'] = [{
                "id": video["id"],
                "title": video["title"],
                "publish_date": video["published_date"],
                "description": video["description"],
                "link": video["link"]
            } for video in search_videos if video['channel']['id'] == channel]

            target_dir = os.path.join(DATA_DIR, slugify(channel_name))
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            json_abs_path = os.path.join(target_dir, 'meta.json')
            json.dump(data, open(json_abs_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            get_youtube_stream(json_abs_path, DATA_DIR)

    def search_youtube_video_by_query(query, channel=None, language=language, limit=limit, api_version='3', verbose=verbose):
        if verbose:
            print(f'[{module}] Start Youtube Search Engine via Data API V{api_version}')
            print(f'[{module}] Query: {query}' + f' | Channel: {channel}' if channel else '')
        youtube = YoutubeDataAPI(constants.api_key, api_version=api_version)
        videos = youtube.search(query, channel_id=channel, max_results=limit, region_code=language)
        if verbose:
            print(f'[{module}] videos found: {len(videos)}')
        return _compute_query_metadata(videos, verbose=verbose)

    return search_youtube_video_by_query(query, channel=channel, language=language, limit=limit, verbose=verbose)


def main():
    print("""
    #######################################
    # Youtube Dataset Collector           #
    # by Dr. Watthanasak Jeamwatthanachai #
    #######################################
    """)

    opts = {
        'language': 'th',
        'limit': 9999,
        'verbose': True,
    }

    search_youtube_video_by_query('', channel='UCovADuA7KBuMFORurTzL86A', **opts)


if __name__ == "__main__":
    main()
