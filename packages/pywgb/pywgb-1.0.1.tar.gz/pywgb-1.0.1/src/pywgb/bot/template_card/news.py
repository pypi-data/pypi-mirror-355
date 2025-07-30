#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Card type message sender

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/6/4 17:21
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from functools import partial
from logging import getLogger
from typing import List

from jmespath import search

from . import TemplateCardKeys, TemplateCardRequirements
from .._abstract import ConvertedData, AbstractBot

logger = getLogger(__name__)


class NewsCardBot(AbstractBot):
    """News Card type message Wecom Group Bot"""

    _VALID_KEYS: List[str] = TemplateCardKeys + [
        "card_image", "image_text_area", "vertical_content_list"
    ]

    @property
    def _doc_key(self) -> str:
        return "图文展示模版卡片"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        reqs = {
            "Both `main_title` and `main_title.title` must be existed":
                partial(
                    search, """
                    main_title == null ||
                    main_title.title == null ||
                    main_title.title == ''
                """),
            "Both `card_image` and `card_image.url` must be existed":
                partial(
                    search, """
                    card_image == null ||
                    card_image.url == null ||
                    card_image.url == ''
                """),
            "When `image_text_area.type` is 1, the `image_text_area.url` must be existed":
                partial(
                    search, """
                    image_text_area.type == `1` &&
                    (image_text_area.url == null || image_text_area.url == '')
                """),
            "When `image_text_area.type` is 2, the `image_text_area.appid` must be existed":
                partial(
                    search, """
                    image_text_area.type == `2` &&
                    (image_text_area.appid == null || image_text_area.appid == '')
                """),
            "The `image_text_area.image_url` must be existed":
                partial(
                    search, """
                    image_text_area != null &&
                    (image_text_area.image_url == null || image_text_area.image_url == '')
                """),
            "The `vertical_content_list.title` must be existed":
                partial(
                    search, """
                    length(
                        (vertical_content_list || `[]`)[?
                            title == null || title == ''
                        ]
                    ) != `0`
                """),
            **TemplateCardRequirements
        }
        for msg, cmd in reqs.items():
            logger.debug("Validating parameter error: %s", msg)
            if cmd(kwargs):
                logger.critical("[NO PASS] Parameter validation error: %s", msg)
                raise ValueError(msg)

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to text card format data.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted data.
        """
        kw_ = {
            key: val for key, val in kwargs.items() if key in self._VALID_KEYS
        }
        result = ({
            "msgtype": "template_card",
            "template_card": {
                "card_type": "news_notice",
                **kw_,
            }
        },)
        return result, kwargs
