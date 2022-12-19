import requests
import os
import re
import html
import json

ARCHIVE = 'https://a.4cdn.org/biz/archive.json'
CATALOG = 'https://a.4cdn.org/biz/catalog.json'


def cleanhtml(raw_html: str) -> str:
    """
    :param raw_html: html code
    :return: text without html code and symbols
    """
    CLEANR = re.compile('<.*?>')
    cleantext = html.unescape(raw_html.replace("<br>", "\n"))
    while "<a" in cleantext:
        a_open_ind = cleantext.find("<a")
        a_close_ind = cleantext.find("</a>")
        if a_open_ind != -1 and a_close_ind != -1:
            cleantext = cleantext[:a_open_ind] + cleantext[a_close_ind + 4:]
        else:
            break
    cleantext = re.sub(CLEANR, '', cleantext)
    return cleantext


def get_image_link(source: dict) -> str:
    ext = source.get("ext")
    i_name = source.get("tim")
    if ext and i_name:
        return f"https://i.4cdn.org/biz/{i_name}{ext}"
    return ""


def get_title(source: dict) -> str:
    return source.get("sub", "")


def get_text(source: dict) -> str:
    text = source.get("com")
    if text:
        return cleanhtml(text)
    return ""


def get_replies(source: list) -> list:
    replies = []
    if "replies" in source[0]:
        for i in source[1:]:
            comment = {
                "text": get_text(i),
                "img_link": get_image_link(i)
            }
            replies.append(comment)
    return replies


def create_file(no: int, directory: str) -> None:
    """
    Creates a file with title, text and link on image of thread and comments with text and image link
    :param no: index of thread (["no"] parameter in API)
    :param directory: directory where to save file
    :return: nothing
    """
    link = fr"https://boards.4channel.org/biz/thread/{no}.json"
    reply = requests.get(link).json()
    if not reply:
        return
    context = {
        "title": get_title(reply["posts"][0]),
        "text": get_text(reply["posts"][0]),
        "img_link": get_image_link(reply["posts"][0]),
        "replies": get_replies(reply["posts"])
    }
    file_path = os.path.join(directory, f"{no}.json")
    with open(file_path, "w") as file:
        json.dump(context, file)


def change_comments(no: int, path: str) -> None:
    """
    Adding new comments to file if new where added
    :param no: index of thread
    :param path: directory where file is located
    :return: nothing
    """
    path = os.path.join(path, f"{no}.json")
    with open(path, "r") as file:
        thread = json.load(file)
    comments = thread["replies"]
    link = fr"https://boards.4channel.org/biz/thread/{no}.json"
    reply = requests.get(link).json()
    if not reply:
        return
    reply = reply["posts"][1:]
    local_rep = len(comments)
    real_rep = len(reply)
    if real_rep > local_rep:
        for i in reply[local_rep:]:
            comment = {
                "text": get_text(i),
                "img": get_image_link(i)
            }
            comments.append(comment)
        thread["replies"] = comments
        with open(path, "w") as file:
            json.dump(thread, file)


def check_catalog() -> None:
    """
    :return: updates files from catalog
    """
    with open("config.json", "r") as file:
        directory = json.load(file)["folder_path"]
    reply = requests.get(CATALOG).json()
    if not reply:
        return
    for i in reply:
        for j in i["threads"]:
            no = j["no"]
            path = os.path.join(directory, f"{no}.json")
            if os.path.exists(path):
                change_comments(no, directory)
            else:
                create_file(no, directory)


def archive_rec() -> None:
    """
    Updating archived threads
    :return: nothing
    """
    with open("config.json", "r") as file:
        config = json.load(file)
    last_local_thread = config["last_archive_element"]
    reply = requests.get(ARCHIVE).json()
    if not reply:
        return
    dif = reply
    for i in range(len(reply) - 1, 0, -1):
        if reply[i] <= last_local_thread:
            dif = reply[i + 1:]
            break
    for i in dif:
        if os.path.exists(os.path.join(config["folder_path"], f"{i}.json")):
            change_comments(i, config["folder_path"])
        else:
            create_file(i, config["folder_path"])
    config["last_archive_element"] = reply[-1]
    with open("config.json", "w") as file:
        json.dump(config, file)


def main():
    try:
        with open("config.json", "r") as file:
            directory = json.load(file)["folder_path"]
        if not os.path.exists(directory):
            os.mkdir(directory)
    except:
        print("Problems with given directory")
    try:
        check_catalog()
        archive_rec()
    except Exception as e:
        pass
