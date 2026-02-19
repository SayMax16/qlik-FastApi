#!/usr/bin/env python3
"""Test UWDJj with bookmark to see total rows."""

import sys
sys.path.insert(0, '/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api')

from src.api.core.config import settings
from src.api.clients.qlik_engine import QlikEngineClient
import time

def main():
    app_id = settings.app_mappings.get("Stock")
    object_id = "UWDJj"
    bookmark_id = "b3d09176-c0ea-4e3c-b153-899394055299"  # 3-month bookmark

    print(f"Testing UWDJj with 3-month bookmark")
    print(f"Object ID: {object_id}")
    print(f"Bookmark ID: {bookmark_id}\n")

    client = QlikEngineClient(settings)
    try:
        # Connect and open app
        client.connect()
        result = client.open_doc(app_id, no_data=False)
        app_handle = result['qReturn']['qHandle']
        print(f"Opened app, handle: {app_handle}")

        # Apply bookmark FIRST
        print(f"\nApplying bookmark...")
        start = time.time()
        client.apply_bookmark(app_handle, bookmark_id)
        print(f"Bookmark applied in {time.time() - start:.2f}s")

        # Get object
        obj_resp = client.send_request("GetObject", [object_id], handle=app_handle)
        obj_handle = obj_resp["qReturn"]["qHandle"]

        # Get layout to see how many rows the object has AFTER bookmark
        layout = client.send_request("GetLayout", [], handle=obj_handle)
        hc = layout.get("qLayout", {}).get("qHyperCube", {})
        total_rows = hc.get("qSize", {}).get("qcy", 0)

        print(f"\nTotal rows in object after bookmark: {total_rows}")

        # Get properties
        props = client.send_request("GetProperties", [], handle=obj_handle)
        hc_def = props.get("qProp", {}).get("qHyperCubeDef", {})
        n_dims = len(hc_def.get("qDimensions", []))
        n_meas = len(hc_def.get("qMeasures", []))

        print(f"Dimensions: {n_dims}, Measures: {n_meas}")

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
