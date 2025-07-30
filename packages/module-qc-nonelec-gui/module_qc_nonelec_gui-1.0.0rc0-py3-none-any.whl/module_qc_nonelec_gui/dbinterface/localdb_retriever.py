from __future__ import annotations


def userinfo_retriever(localdbtools, username):
    return localdbtools.viewer.user.find_one({"username": username})
