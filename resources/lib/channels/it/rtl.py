# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script

from resources.lib import web_utils, resolver_proxy
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment
from resources.lib.web_utils import html_parser

PATTERN_MEDIA_OBJECT = re.compile(r'data-media-object="(.*?)"')
PATTERN_BACKGROUND_IMAGE_URL = re.compile(r'url\((.*)\)')

URL_ROOT = "https://play.rtl.it"

DEFAULT_IMAGE = get_item_media_path('channels/it/rtl-1025-radiovisione.png')


@Route.register
def list_lives(plugin, item_id, **kwargs):
    root = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1).parse()
    channels = root.findall(".//div[@data-media-type='SectionItem']")

    if len(channels) == 0:
        return False

    for channel in channels:

        live_image = DEFAULT_IMAGE

        live_url_anchor = channel.find('.//a')
        if live_url_anchor is None:
            continue

        live_url = URL_ROOT + live_url_anchor.get('href')

        resp = urlquick.get(live_url)
        media_objects = PATTERN_MEDIA_OBJECT.findall(resp.text)
        if len(media_objects) == 0:
            continue
        media_object = html_parser.unescape(media_objects[0])
        json_media_object = json.loads(media_object)
        live_plot = live_title = json_media_object['mediaInfo']['title']

        style = channel.find('.//img').get('style')
        img_array = PATTERN_BACKGROUND_IMAGE_URL.findall(style)
        if len(img_array) > 0:
            live_image = img_array[0]

        on_focus = channel.find(".//div[@class='on-focus-state-info']")
        if on_focus is not None:
            img = on_focus.find(".//img")
            if img is not None:
                live_image = img.get('src')
            live_plot = on_focus.find(".//div[@class='info-title']").text

        url = json_media_object['mediaInfo']['uri']

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = item.art['landscape'] = live_image
        item.info['plot'] = live_plot
        item.set_callback(get_live_url, url=url)
        item_post_treatment(item, is_playable=True)
        yield item


@Resolver.register
def get_live_url(plugin, url, **kwargs):
    return resolver_proxy.get_stream_ia_or_default(plugin, video_url=url, manifest_type="hls")
