#!/usr/bin/env python3
"""Get all bookmarks in Stock app."""

import sys
sys.path.insert(0, '/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api')

from src.api.core.config import settings
from src.api.clients.qlik_engine import QlikEngineClient

def main():
    app_id = settings.app_mappings.get("Stock")
    print(f"Getting bookmarks from Stock app: {app_id}\n")

    client = QlikEngineClient(settings)
    try:
        client.connect()
        result = client.open_doc(app_id, no_data=True)
        app_handle = result['qReturn']['qHandle']

        all_infos = client.send_request("GetAllInfos", [], handle=app_handle)
        all_objects = all_infos.get("qInfos", [])

        bookmark_infos = [obj for obj in all_objects if obj.get("qType") == "bookmark"]

        print(f"Found {len(bookmark_infos)} bookmark(s):\n")

        for i, bm_info in enumerate(bookmark_infos):
            bm_id = bm_info.get("qId")
            try:
                get_bm = client.send_request("GetBookmark", [bm_id], handle=app_handle)
                if "qReturn" in get_bm:
                    bm_handle = get_bm["qReturn"]["qHandle"]
                    layout = client.send_request("GetLayout", [], handle=bm_handle)

                    qLayout = layout.get("qLayout", {})
                    qMeta = qLayout.get("qMeta", {})
                    title = qMeta.get("title", "Untitled")

                    print(f"[{i+1}] ID: {bm_id}")
                    print(f"    Title: {title}")
                    print()
            except Exception as e:
                print(f"[{i+1}] ID: {bm_id}")
                print(f"    Could not get details: {e}")
                print()

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
