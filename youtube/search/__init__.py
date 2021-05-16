from youtube.search.extras import Video, Playlist, Suggestions
from youtube.search.internal.constants import *
from youtube.search.search import Search, VideosSearch, ChannelsSearch, PlaylistsSearch, CustomSearch
from youtube.search.streamurlfetcher import StreamURLFetcher

__title__ = 'youtube-search-python'
__version__ = '1.4.5'
__author__ = 'alexmercerind'
__license__ = 'MIT'

""" Deprecated. Present for legacy support. """
from youtube.search.legacy import SearchVideos, SearchPlaylists
from youtube.search.legacy import SearchVideos as searchYoutube
