# This file is distributed as a part of the polygon project (justaprudev.github.io/polygon)
# By justaprudev

import re
from pathlib import Path

# db functions
def cache_filters() -> dict:
    filters = db.get(NAME)
    if filters is None:
        set_filters({})
        filters = cache_filters()
    return filters


def get_filters(chat_id) -> dict:
    filters = FILTERS_CACHE.get(chat_id, None)
    if filters is None:
        FILTERS_CACHE[chat_id] = {}
        filters = FILTERS_CACHE[chat_id]
    return filters


def add_filter(chat_id, key, content):
    filters = get_filters(chat_id)
    filters[key] = content
    set_filters(FILTERS_CACHE)
    return True


def remove_filter(chat_id, key):
    filters = get_filters(chat_id)
    if key in filters:
        del filters[key]
        set_filters(FILTERS_CACHE)
        return True
    return False


def clear_filters(chat_id):
    if chat_id in FILTERS_CACHE:
        del FILTERS_CACHE[chat_id]
    set_filters(FILTERS_CACHE)
    return True


def set_filters(filters: dict):
    db.add(name=NAME, value=filters)

def isfileid(content):
    return isinstance(content, int)


# Constants
NAME = Path(__file__).stem
FILTERS_CACHE = cache_filters()

@polygon.on()
@polygon.on(incoming=True)
async def filter(e):
    chat_id = str(e.chat_id)
    message = e.text.lower()
    if chat_id in FILTERS_CACHE.keys():
        for key, content in get_filters(chat_id).items():
            # if key in message:
            if " " in key:
                pattern = re.compile(key)
            else:
                pattern = re.compile(fr"\b{key}\b")
            if pattern.search(message):
                if isfileid(content):
                    f = await polygon.get_messages(polygon.user.id, ids=content)
                    await polygon.forward_messages(e.chat_id, f)  # Forwarding is fast
                    return
                await e.reply(content)


@polygon.on(pattern="filter ?(.*);+?(.*)")
async def addfilter(e):
    chat_id = str(e.chat_id)
    key = e.pattern_match.group(1)
    content = e.pattern_match.group(2)
    reply = await e.get_reply_message()
    if not key:
        await e.edit("`What do you want to filter?`")
        return
    key = key.lower()
    if not content:
        if reply:
            if reply.media:
                await e.edit("`Saving file..`")
                f = await polygon.forward_messages(
                    polygon.user.id, reply
                )  # Forwarding is fast
                content = int(f.id)
                await f.reply(
                    f"`[DO NOT DELETE]`\
                    \n**This file was saved by polygon**\
                    \n**key:** `{key}`\
                    \n**id:** `{content}`"
                )
            else:
                content = reply.text
        else:
            await e.edit("`What do you want to filter it with?`")
            return
    add_filter(chat_id, key, content)
    await e.edit(f"**Started filtering** `{key}` **in this chat successfully!**")


@polygon.on(pattern="stop ?(.*)")
async def removefilter(e):
    chat_id = str(e.chat_id)
    key = e.pattern_match.group(1)
    if not key:
        clear_filters(chat_id)
        await e.edit("**Stopped all filters in this chat successfully!**")
        return
    key = key.lower()
    if remove_filter(chat_id, key):
        await e.edit(f"**Stopped filter** `{key}` in this chat **successfully!**")
        return
    await e.edit(f"`{key}` **is not being filtered in this chat!**")


@polygon.on(pattern="filters")
async def filters(e):
    chat_id = str(e.chat_id)
    filters = get_filters(chat_id)
    if not filters:
        return await e.edit("`There are no filters in this chat!`")
    message = "**All filters in this chat:**\n\n" + "\n".join([f"~` {key}`" for key in filters])
    await e.edit(message)
