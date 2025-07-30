# pywgb
Wecom(A.K.A. WeChat Work) Group Bot python API. [![codecov](https://codecov.io/gh/ChowRex/pywgb/graph/badge.svg?token=1SDIUB46RU)](https://codecov.io/gh/ChowRex/pywgb)

## Homepage

### Github

> [ChowRex/pywgb: Wecom(A.K.A Wechat Work) Group Bot python API.](https://github.com/ChowRex/pywgb)

### Pypi

> [pywgb · PyPI](https://pypi.org/project/pywgb/)

## How to use

### Pre-conditions

1. Create a [Wecom Group Bot](https://qinglian.tencent.com/help/docs/2YhR-6/).

2. Copy the webhook URL or just the `key`. It **MUST** contains an [UUID (8-4-4-4-12)](https://en.wikipedia.org/wiki/Universally_unique_identifier), like:

   - `Webhook`: *https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=UUID*
   - `Key`: *UUID*

3. Install this package: 

    ```bash
    # Normally use this if you won't send voice message
    pip install -U pywgb
    # You can install full version by this
    pip install -U "pywgb[all]"
    ```

### Send messages

Create a instance of `SmartBot`

```python
from pywgb import SmartBot

KEY = "PASTE_YOUR_KEY_OR_WEBHOOKURL_HERE"
bot = SmartBot(KEY)

```

#### Basic usage

##### Text

```python
msg = "This is a test Text message."
bot.send(msg)

# If you want to send message and mention someone at the same time, refer this.
kwargs = {
  "mentioned_list": [
    # If you know the userid
    "userid",
    # Use below for ALL people
    "@all",
  ],
  "mentioned_mobile_list": [
    # If you know the phone number
    "13800001111",
    # Use below for ALL people
    "@all",
  ]
}
msg = "Alert, this is an important message."
bot.send(msg, **kwargs)

```

##### Markdown

```python
col = [bot.markdown_feature.green, bot.markdown_feature.gray, bot.markdown_feature.orange]
markdown = ''.join(col[idx % 3](ltr) for idx, ltr in enumerate("colorful"))
markdown = f"""
# TESTING

> Author: **Rex**

This is a {markdown} Markdown message
"""
bot.send(markdown)

```

##### News

```python
articles = [
    {
        "title": "This is a test news",
        "description": "You can add description here",
        "url": "www.tencent.com",
        # Here is the link of picture
        "picurl": "https://www.tencent.com/img/index/tencent_logo.png"
    },
]
bot.send(articles=articles)

```

##### Image

```python
image = "Path/To/Your/Image.png" or "Path/To/Your/Image.jpg"
bot.send(file_path=image)

```

##### Voice

📢 You must install **FULL** version to avoid warning prompt.

```python
voice = "Path/To/Your/Voice.amr"  # BE ADVISED: ONLY support amr file
bot.send(file_path=voice)

```

##### File

```python
file = "Path/To/Your/File.suffix"
bot.send(file_path=file)

```

#### Advanced usage

##### Upload temporary media *(Materials only available in 3 days)*

```python
file = "Path/To/Your/File.suffix"
media_id = bot.upload(file)
print(media_id)

```

##### TextTemplateCard *(Need more detail? click [here](https://developer.work.weixin.qq.com/document/path/99110#%E6%96%87%E6%9C%AC%E9%80%9A%E7%9F%A5%E6%A8%A1%E7%89%88%E5%8D%A1%E7%89%87).)*

```python
kwargs = {
    "main_title": {
        "title": "Test message",
        "desc": "This is a test template text card message"
    },
    "emphasis_content": {
        "title": "100",
        "desc": "No meaning"
    },
    "quote_area": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
        "title": "Title reference",
        "quote_text": "Hello\nWorld!"
    },
    "sub_title_text": "This is sub-title",
    "horizontal_content_list": [{
        "keyname": "Author",
        "value": "Rex"
    }, {
        "keyname": "Google",
        "value": "Click to go",
        "type": 1,
        "url": "https://google.com"
    }],
    "jump_list": [{
        "type": 1,
        "url": "https://bing.com",
        "title": "Bing"
    }],
    "card_action": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
    }
}
bot.send(**kwargs)

```

##### NewsTemplateCard *(Need more detail? click [here](https://developer.work.weixin.qq.com/document/path/99110#%E5%9B%BE%E6%96%87%E5%B1%95%E7%A4%BA%E6%A8%A1%E7%89%88%E5%8D%A1%E7%89%87).)*

```python
kwargs = {
    "source": {
        "icon_url":
            "https://wework.qpic.cn/wwpic/252813_jOfDHtcISzuodLa_1629280209/0",
        "desc":
            "This is for testing",
        "desc_color":
            0
    },
    "main_title": {
        "title": "Test message",
        "desc": "This is a test template news card message"
    },
    "card_image": {
        "url":
            "https://wework.qpic.cn/wwpic/354393_4zpkKXd7SrGMvfg_1629280616/0",
        "aspect_ratio":
            2.25
    },
    "image_text_area": {
        "type":
            1,
        "url":
            "https://work.weixin.qq.com",
        "title":
            "Welcom to use pywgb",
        "desc":
            "This is a test message",
        "image_url":
            "https://wework.qpic.cn/wwpic/354393_4zpkKXd7SrGMvfg_1629280616/0"
    },
    "quote_area": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
        "title": "Title reference",
        "quote_text": "Hello\nWorld!"
    },
    "vertical_content_list": [{
        "title": "Hi, there",
        "desc": "Welcome to use"
    }],
    "horizontal_content_list": [{
        "keyname": "Author",
        "value": "Rex"
    }, {
        "keyname": "Google",
        "value": "Click to go",
        "type": 1,
        "url": "https://google.com"
    }],
    "jump_list": [{
        "type": 1,
        "url": "https://bing.com",
        "title": "Bing"
    }],
    "card_action": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
    }
}
bot.send(**kwargs)

```

#### Use the specified bot

You can refer below to use specify kind of bot.

```python
from pywgb.bot import TextBot, MarkdownBot, ImageBot, NewsBot
from pywgb.bot import FileBot, VoiceBot, TextCardBot, NewsCardBot

KEY = "PASTE_YOUR_KEY_OR_WEBHOOKURL_HERE"

bot_type = TextBot
bot = bot_type(Key)
bot.send("Some thing here")
```

This might be useful when you want to send `voice`or `image` as a file *(SmartBot won't send image or voice as file)*.

```python
from pywgb.bot import FileBot

KEY = "PASTE_YOUR_KEY_OR_WEBHOOKURL_HERE"

voice = "Path/To/Your/Voice.amr"
image = "Path/To/Your/Image.png" or "Path/To/Your/Image.jpg"

bot = FileBot(KEY)
bot.send(file_path=voice)
bot.send(file_path=image)
```

## Official Docs

> **Only Chinese** doc: [群机器人配置说明 - 文档 - 企业微信开发者中心](https://developer.work.weixin.qq.com/document/path/99110)

## Roadmap

- [x] v0.0.1: 🎉 Initial project. Offering send `Text` and `Markdown` type message.
- [x] v0.0.2: 🖼️ Add `Image` type message support;

  - Add overheat detect function and unified exception handling
- [x] v0.0.3: 📰 Add `News` type message support;

  - Move bots into a new module: `bot`
- [x] v0.0.4: 📂 Add `File` type message support;

    - Refactor `bot` module
- [x] v0.0.5: 🗣️ Add `Voice` type message support.
    - Refactor `deco` module
    - Add `verify_file` decorator
    - Introverted parameters check errors
    - Add more content into README.md
- [x] v0.0.6: 🩹 Add `Voice` and `File` type size check.
- [x] v0.0.7: 🗒️ Add `TextCard` type message support.
- [x] v0.0.8: 🗃️ Add `NewsCard` type message support.
- [x] v0.0.9: ♻️ Refactor code.
- [x] v0.1.0: 🔧 Fix color bug when use markdown type
- [x] v0.1.1: ⏺️ Refactor all code logic again, I don't like mess and complex.
- [x] v0.1.2: 💪 Add a SmartBot class

    - Add a SmartBot class
    - Enhanced `markdown` bot class
    - Add a txt file for SmartBot testing `File` type
    - Add empty message verify for Text and Markdown
    - Add a new markdown test unit
    - Fully test SmartBot class
- [x] v1.0.0: 👍 First FULL capacity stable version release.Fix bugs and so on.
- [x] v1.0.1: 🐛 Fix some bugs and fulfill coverage.

