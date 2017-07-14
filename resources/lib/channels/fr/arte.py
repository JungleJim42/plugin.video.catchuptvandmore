# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import json
import xbmcgui
#import m3u8
from resources.lib import utils
from resources.lib import common

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.addon.initialize_gettext()

# TODO
#   List emissions
#   Most recent
#   Most viewed

url_replay = 'https://www.arte.tv/papi/tvguide/videos/' \
             'ARTE_PLUS_SEVEN/%s.json?includeLongRights=true'

url_live_arte_fr = 'http://artelive-lh.akamaihd.net/i/' \
		   'artelive_fr@344805/index_1_av-b.m3u8?sd=10&rebase=on'
		   
url_live_arte_de = 'http://artelive-lh.akamaihd.net/i/' \
		   'artelive_de@393591/index_1_av-b.m3u8?sd=10&rebase=on'
# Valid languages: F or D


def channel_entry(params):
    # A decommencter quand on es bloquer "Live FR"
    #return get_video_url(params)
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
	return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)
    

#@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []
    emissions_list = []
    categories = {}

    desired_language = common.plugin.get_setting(
        params.channel_id + '.language')

    if desired_language == 'FR':
        desired_language = 'F'
    else:
        desired_language = 'D'

    file_path = utils.download_catalog(
        url_replay % desired_language,
        '%s_%s.json' % (params.channel_name, desired_language)
    )
    file_replay = open(file_path).read()
    json_parser = json.loads(file_replay)

    for emission in json_parser['paginatedCollectionWrapper']['collection']:
        emission_dict = {}
        emission_dict['duration'] = emission['videoDurationSeconds']
        emission_dict['video_url'] = emission['videoPlayerUrl'].encode('utf-8')
        emission_dict['image'] = emission['programImage'].encode('utf-8')
        try:
            emission_dict['genre'] = emission['genre'].encode('utf-8')
        except:
            emission_dict['genre'] = 'Unknown'
        try:
            emission_dict['director'] = emission['director'].encode('utf-8')
        except:
            emission_dict['director'] = ''
        emission_dict['production_year'] = emission['productionYear']
        emission_dict['program_title'] = emission['VTI'].encode('utf-8')
        try:
            emission_dict['emission_title'] = emission['VSU'].encode('utf-8')
        except:
            emission_dict['emission_title'] = ''

        emission_dict['category'] = emission['VCH'][0]['label'].encode('utf-8')
        categories[emission_dict['category']] = emission_dict['category']
        emission_dict['aired'] = emission['VDA'].encode('utf-8')
        emission_dict['playcount'] = emission['VVI']

        try:
            emission_dict['desc'] = emission['VDE'].encode('utf-8')
        except:
            emission_dict['desc'] = ''

        emissions_list.append(emission_dict)

    with common.plugin.get_storage() as storage:
        storage['emissions_list'] = emissions_list

    for category in categories.keys():

        shows.append({
            'label': category,
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_videos_cat',
                category=category,
                window_title=category
            ),
        })
    
    shows.append({
	'label' : 'Live',
	'url': common.plugin.get_url(
	    action='channel_entry',
	    next='live_cat',
	    category='live arte',
	    window_title='live'
	),
    })

    return common.plugin.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


#@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []
    with common.plugin.get_storage() as storage:
        emissions_list = storage['emissions_list']

    if params.next == 'list_videos_cat':
        for emission in emissions_list:
            if emission['category'] == params.category:
                if emission['emission_title']:
                    title = emission['program_title'] + ' - [I]' + \
                        emission['emission_title'] + '[/I]'
                else:
                    title = emission['program_title']
                aired = emission['aired'].split(' ')[0]
                aired_splited = aired.split('/')
                day = aired_splited[0]
                mounth = aired_splited[1]
                year = aired_splited[2]
                # date : string (%d.%m.%Y / 01.01.2009)
                # aired : string (2008-12-07)
                date = '.'.join((day, mounth, year))
                aired = '-'.join((year, mounth, day))
                info = {
                    'video': {
                        'title': title,
                        'plot': emission['desc'],
                        'aired': aired,
                        'date': date,
                        'duration': emission['duration'],
                        'year': emission['production_year'],
                        'genre': emission['genre'],
                        'playcount': emission['playcount'],
                        'director': emission['director'],
                        'mediatype': 'tvshow'
                    }
                }

                # Nouveau pour ajouter le menu pour télécharger la vidéo
                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.plugin.get_url(
                        action='download_video',
                        url=emission['video_url']) + ')'
                )
                context_menu.append(download_video)
                # Fin

                videos.append({
                    'label': title,
                    'thumb': emission['image'],
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='play_replay',
                        url=emission['video_url'],
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu  #  A ne pas oublier pour ajouter le bouton "Download" à chaque vidéo
                })

        return common.plugin.create_listing(
            videos,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_DATE,
                common.sp.xbmcplugin.SORT_METHOD_DURATION,
                common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
                common.sp.xbmcplugin.SORT_METHOD_GENRE,
                common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED
            ),
            content='tvshows')

#@common.plugin.cached(common.cache_time)
def list_live(params):
    lives = []
    
    lives.append({
	'label': 'Live FR',
	'url' : common.plugin.get_url(
	    action='channel_entry',
	    next='play_live',
	    url=url_live_arte_fr,
	),
	'is_playable': True
    })
    
    lives.append({
	'label': 'Live DE',
	'url' : common.plugin.get_url(
	    action='channel_entry',
	    next='play_live',
	    url=url_live_arte_de,
	),
	'is_playable': True
    })
    
    return common.plugin.create_listing(
	lives)

#@common.plugin.cached(common.cache_time)
def get_video_url(params):
    
    if params.next == 'play_replay':
	file_medias = utils.get_webcontent(
	    params.url)
	json_parser = json.loads(file_medias)

	url_selected = ''    
	video_streams = json_parser['videoJsonPlayer']['VSR']
	
	desired_quality = common.plugin.get_setting('quality')

	if desired_quality == "DIALOG":
	    all_datas_videos = []

	    for video in video_streams:
		if not video.find("HLS"):
			datas = json_parser['videoJsonPlayer']['VSR'][video]
			new_list_item = xbmcgui.ListItem()
			new_list_item.setLabel(datas['mediaType'] + " (" + datas['versionLibelle'] + ")")
			new_list_item.setPath(datas['url'])
			all_datas_videos.append(new_list_item)

	    seleted_item = xbmcgui.Dialog().select("Choose Stream", all_datas_videos)

	    url_selected = all_datas_videos[seleted_item].getPath().encode('utf-8')
	
	elif desired_quality == "BEST":
	    url_selected = video_streams['HTTP_MP4_SQ_1']['url'].encode('utf-8')
	else:
	    url_selected = video_streams['HLS_SQ_1']['url'].encode('utf-8')

	return url_selected
    elif params.next == 'play_live':
	return params.url

