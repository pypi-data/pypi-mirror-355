#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text type message sender

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/5/27 14:53
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from ._abstract import ConvertedData, AbstractBot
from .markdown import MarkdownBot


class TextBot(AbstractBot):
    """Text type message Wecom Group Bot"""

    _OPTIONAL_ARGS = ["mentioned_list", "mentioned_mobile_list"]

    @property
    def _doc_key(self) -> str:
        return "文本类型"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        # pylint: disable=protected-access
        MarkdownBot(self.key)._verify_arguments(*args, **kwargs)
        for optional in self._OPTIONAL_ARGS:
            if optional not in kwargs:
                continue
            err_msg = f"The {optional} parameter should be a list of strings."
            if not isinstance(data := kwargs[optional], list):
                raise ValueError(err_msg)
            if not all(isinstance(_, str) for _ in data):
                raise ValueError(err_msg)

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to text format data.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted data.
        """
        mentioned_list: list = kwargs.get("mentioned_list", [])
        mentioned_mobile_list: list = kwargs.get("mentioned_mobile_list", [])
        result = ({
            "msgtype": "text",
            "text": {
                "content": args[0].strip(),
                "mentioned_list": mentioned_list,
                "mentioned_mobile_list": mentioned_mobile_list
            }
        },)
        return result, kwargs
