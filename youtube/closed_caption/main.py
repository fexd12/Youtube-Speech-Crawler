#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: ./nb/main.ipynb

import copy
import html
import json
# dealing with transcript
import math
import re
import socket
import sys
import urllib
from functools import partial
from pprint import pprint
from typing import Union
from xml.dom.minidom import parseString

import fire
import requests

import youtube.closed_caption.common as common

if __name__ == '__main__':
    sys.path.append('..')


def pj(*args, **kargs):
    if common.IN_JUPYTER:
        pprint(*args, **kargs)


perr = partial(print, "ERR: ")
socket.setdefaulttimeout(5.)


# dealing with xml.dom
def getVal(dom, key):
    att = dom.attributes[key]
    return att.value


def eachTxt(txt, remove_font_tag):
    start = getVal(txt, 'start')
    dur = getVal(txt, 'dur')
    if txt.firstChild is None:
        # fix dl-youtube-cc.exe Zd14s2WW-Tc --caption_num=1
        txt = ""
    else:
        txt = html.unescape((txt.firstChild.data))
        if remove_font_tag:
            txt = re.sub(r'</?font[^>]*>', '', txt)
    return {
        "start": start,
        "dur": dur,
        "text": txt
    }


def get_data(link):
    data = requests.get(link)
    data = data.text
    return data


class CaptionNotAvailableException(Exception):
    pass


def get_tracks_title(data):
    decodedData = urllib.parse.unquote(data)
    if 'captionTracks' not in decodedData:
        perr("no caption available for this video ;( following are message from youtube")
        perr(re.findall('playabilityStatus.*?}', decodedData))
        raise CaptionNotAvailableException()
    match = re.search(r'({"captionTracks":.*isTranslatable":(true|false)}])', decodedData)
    match = match.group(1)
    match = f"{match}}}"
    captionTracks = json.loads(match)['captionTracks']
    match = re.search(r'title":"(.*?)","lengthSeconds":', decodedData)
    title = match.group(1)
    return captionTracks, title


def parseTranscript(transcript, remove_font_tag=True):
    try:
        dom = parseString(transcript.text)
    except:
        perr("check your lang code")
        perr("server response")
        perr(transcript.text)
        exit(1)
    texts = dom.getElementsByTagName('text')

    _eachTxt = partial(eachTxt, remove_font_tag=remove_font_tag)
    texts = list(map(_eachTxt, texts, ))
    return texts


def each_sent(o, file=sys.stdout):
    start = o['start']
    start = float(start)
    minute = math.floor(start / 60)
    second = math.floor(start % 60)
    p = partial(print, file=file)
    p(f"---------{minute:02d}:{second:02d}----------")
    p(o['text'])
    translate_text = o.get('translate_text', None)
    if translate_text:
        p(translate_text)


# dealing with valid filename
# https://github.com/django/django/blob/master/django/utils/text.py
def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def merge_subtitle(subtitle, subtitle_cn):
    """
    merge subtitle_cn(traslation) to subtitle(origin).
    cc and translated cc aren't always align,
    I found at least in cn and ja, translated cc are less than cc
    see  videoID='HSz7Q4YnQ_M'
    cc and translated cc aren't always equal in time see wgNiGj1nGYE for translation ja
    """
    subtitle = copy.deepcopy(subtitle)  # original transcript
    subtitle_cn = copy.deepcopy(subtitle_cn)  # translation script

    TRANSLATE_TEXT = "translate_text"
    TEXT = "text"
    START = "start"

    # NOTE not sure how to merge them properly

    # indexer for subtitle
    sub_p = 0
    sub_p_cn = 0

    while sub_p < len(subtitle) and sub_p_cn < len(subtitle_cn):

        sub = subtitle[sub_p]
        sub_cn = subtitle_cn[sub_p_cn]

        if TRANSLATE_TEXT not in sub: sub[TRANSLATE_TEXT] = ""

        if float(sub[START]) >= float(sub_cn[START]):
            # sub goes first, being chased by sub_cn

            # for separating the sentence
            if len(sub[TRANSLATE_TEXT]) != 0: sub[TRANSLATE_TEXT] += "\n"

            sub[TRANSLATE_TEXT] += sub_cn[TEXT]

            sub_p_cn += 1

        else:
            sub_p += 1

    # add empty field for subitle
    while sub_p < len(subtitle):
        assert sub_p_cn == len(subtitle_cn)

        sub = subtitle[sub_p]
        if TRANSLATE_TEXT not in sub: sub[TRANSLATE_TEXT] = ""
        sub_p += 1

    # add the rest of subtitle_cn to the last one of subtitle
    while sub_p_cn < len(subtitle_cn):
        assert sub_p == len(subtitle)

        sub = subtitle[-1]

        if TRANSLATE_TEXT not in sub: sub[TRANSLATE_TEXT] = ""

        if len(sub[TRANSLATE_TEXT]) != 0: sub[TRANSLATE_TEXT] += "\n"

        sub[TRANSLATE_TEXT] += sub_cn[TEXT]
        sub_p_cn += 1

    assert sub_p == len(subtitle)
    assert sub_p_cn == len(subtitle_cn)

    return subtitle


def format_caption(caption):
    ret = f"{caption['vssId']:8s} {caption['name']['simpleText']}"
    if 'a.' in caption['vssId']:
        ret += ' automatically generated by youtube'
    return ret


def parseVideoID(videoID):
    if 'youtu' in videoID:
        videoID = re.search('v=([^&]+)', videoID).group(1)

    video_link = f'https://www.youtube.com/watch?v={videoID}'
    data_link = f"https://youtube.com/get_video_info?video_id={videoID}"
    return videoID, video_link, data_link


def main(videoID: str, translation: Union[str, bool] = 'zh-Hans', caption_num: int = 0, caption_num_second: int = None,
         output_file: str = None, save_to_file: bool = True, to_json: bool = False, remove_font_tag: bool = True, ):
    """
    download youtube closed caption(subtitles) by videoID

    Examples:
    dl-youtube-cc -h # to see this helpful infomation
    dl-youtube-cc wgNiGj1nGYE --translation 'ja' # use japanese translation, see ./lang_code for full list
    dl-youtube-cc wgNiGj1nGYE --caption_num=1 --translation 'ja' # choose the caption num for original transcript and use japanese translation,
    dl-youtube-cc wgNiGj1nGYE --caption_num=1 --caption_num_second=2 # manually choose the original and translation transcript from available caption list
    dl-youtube-cc wgNiGj1nGYE --translation False # without translation
    dl-youtube-cc wgNiGj1nGYE --save_to_file=False # print stuff in console
    dl-youtube-cc wgNiGj1nGYE --output_file='test.txt' # print stuff in named file
    dl-youtube-cc wgNiGj1nGYE --to_json=True # print stuff in json

    Argument:
    videoID : the video link or the id of youtube video, the string after 'v=' in a youtube video link
    translation : which will be displayed as original transcript, default to 'zh-Hans' for simplified Chinese, see ./lang_code.json for full list, or pass False to disable translation
    caption_num : choose the caption which will be displayed as original transcript
    caption_num_second : will surpass translation option, choose the caption which will be displayed as translation transcript
    output_file : default to video title
    save_to_file : pass False to print in console
    to_json: pass True to export caption to json
    remove_font_tag: remove font tag
    """
    videoID, video_link, data_link = parseVideoID(videoID)
    data = get_data(data_link)
    captionTracks, title = None, None
    try:
        captionTracks, title = get_tracks_title(data)
    except:
        perr("can't not retrive caption, visit ", data_link, " for detail")
        raise

    info = partial(print, "INFO: ")

    info("available caption(s):")
    for i, caption in enumerate(captionTracks):
        mark = '⭕'
        if caption_num == i: mark = '✔ as original'
        if caption_num_second == i: mark = '✔ as translation'
        notice = f"{mark}"
        info(notice, f"#{i}.", format_caption(caption))
    info("✔ marks chosen one in 0-index")
    info("given by --caption_num default to 0 as original")
    if caption_num_second is None: info(
        "you may use --caption_num_second intead of --translation to spefify translation transript")
    get_caption_url = lambda i: captionTracks[i]["baseUrl"]

    # as original caption
    caption = captionTracks[caption_num]
    baseUrl = caption['baseUrl']
    transcript = requests.get(baseUrl)
    #     info('using',f"{caption_num}.", format_caption(caption))

    _parseTranscript = partial(parseTranscript, remove_font_tag=remove_font_tag)
    subtitle = _parseTranscript(transcript, )
    sent_subtitle = subtitle

    output_json = {"original": subtitle}

    if translation or caption_num_second:
        if translation: baseUrl = caption['baseUrl'] + '&tlang=' + translation
        if caption_num_second: baseUrl = get_caption_url(caption_num_second)
        transcript = requests.get(baseUrl)
        subtitle_cn = _parseTranscript(transcript)
        merged_subtitle = merge_subtitle(subtitle, subtitle_cn)
        sent_subtitle = merged_subtitle
        output_json = {
            "original": subtitle,
            "translation": subtitle_cn,
            # note that it's not guaranteed to be aligned.
            "merged": merged_subtitle,
        }

    ######################## save to file

    f = sys.stdout
    if save_to_file:
        if output_file is None:
            if to_json:
                output_file = get_valid_filename(f'{title}.json')
            else:
                output_file = get_valid_filename(f'{title}.txt')
        f = open(output_file, 'w', encoding='UTF-8')
        info("Save to ", output_file)

    if to_json:
        json.dump(
            output_json
            , f, indent=4, ensure_ascii=False)
        return

    pfile = partial(print, file=f)
    pfile(video_link, file=f)
    for sent in sent_subtitle:
        each_sent(sent, file=f)
        pfile()


def set_fire(fn):
    if common.IN_TRAVIS or common.IN_JUPYTER:
        return
    fire.Fire(fn)


if __name__ == '__main__':
    if common.IN_TRAVIS or common.IN_JUPYTER:
        pass
    else:
        set_fire(main)
fire_main = partial(set_fire, main)
