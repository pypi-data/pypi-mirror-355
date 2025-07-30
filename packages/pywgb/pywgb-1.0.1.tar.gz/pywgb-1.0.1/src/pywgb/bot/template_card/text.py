#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Card type message sender

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/6/4 10:09
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from functools import partial
from logging import getLogger
from typing import List

from jmespath import search

from . import TemplateCardKeys, TemplateCardRequirements
from .._abstract import ConvertedData, AbstractBot

logger = getLogger(__name__)


class TextCardBot(AbstractBot):
    """Text Card type message Wecom Group Bot"""

    _VALID_KEYS: List[str] = TemplateCardKeys + [
        "emphasis_content", "sub_title_text"
    ]

    @property
    def _doc_key(self) -> str:
        return "文本通知模版卡片"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        reqs = {
            "Either `main_title.title` should be existed or `sub_title_text` be existed":
                partial(
                    search, """
                    (main_title.title == null || main_title.title == '') &&
                    (sub_title_text == null || sub_title_text == '')
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
                "card_type": "text_notice",
                **kw_,
            }
        },)
        return result, kwargs
