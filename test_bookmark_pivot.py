#!/usr/bin/env python3
"""Test bookmark with pivot table object."""

import sys
sys.path.insert(0, '/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api')

from src.api.core.config import settings
from src.api.clients.qlik_engine import QlikEngineClient
import time

def main():
    app_id = settings.app_mappings.get("Stock")
    object_id = "5f78a4f8-3ea6-40b2-8ed8-9eeef2bf9e21"  # Pivot table
    bookmark_id = "0ff80188-58b9-4684-8d72-2b7efe1ee395"  # 1-month bookmark

    print(f"Testing object '{object_id}' with bookmark '{bookmark_id}'")
    print(f"App ID: {app_id}\n")

    client = QlikEngineClient(settings)
    try:
        # Connect and open app
        client.connect()
        result = client.open_doc(app_id, no_data=False)
        app_handle = result['qReturn']['qHandle']
        print(f"Opened app, handle: {app_handle}")

        # Get object info
        obj_resp = client.send_request("GetObject", [object_id], handle=app_handle)
        obj_handle = obj_resp["qReturn"]["qHandle"]

        obj_info = client.send_request("GetInfo", [], handle=obj_handle)
        obj_type = obj_info.get("qInfo", {}).get("qType", "unknown")
        print(f"Object type: {obj_type}\n")

        # Apply bookmark
        print(f"Applying bookmark '{bookmark_id}'...")
        start_time = time.time()
        apply_result = client.apply_bookmark(app_handle, bookmark_id)
        bookmark_time = time.time() - start_time
        print(f"Bookmark applied in {bookmark_time:.2f}s: {apply_result}\n")

        # Get layout to see total rows (like the API does - THIS IS SLOW!)
        print("Calling GetLayout...")
        layout_start = time.time()
        layout = client.send_request("GetLayout", [], handle=obj_handle)
        layout_time = time.time() - layout_start
        print(f"GetLayout took {layout_time:.2f}s")

        hc = layout.get("qLayout", {}).get("qHyperCube", {})
        total_rows = hc.get("qSize", {}).get("qcy", 0)
        print(f"Total rows in pivot after bookmark: {total_rows}\n")

        # Try to fetch small amount of data
        print("Fetching first 10 rows...")
        fetch_start = time.time()

        # Get properties for dimension/measure info (like the API does)
        print("Calling GetProperties...")
        props_start = time.time()
        props = client.send_request("GetProperties", [], handle=obj_handle)
        props_time = time.time() - props_start
        print(f"GetProperties took {props_time:.2f}s")

        hc_def = props.get("qProp", {}).get("qHyperCubeDef", {})
        n_dims = len(hc_def.get("qDimensions", []))
        n_meas = len(hc_def.get("qMeasures", []))
        print(f"Dimensions: {n_dims}, Measures: {n_meas}")

        data_resp = client.send_request(
            "GetHyperCubePivotData",
            [
                "/qHyperCubeDef",
                [{"qLeft": 0, "qTop": 0, "qWidth": max(n_meas, 1), "qHeight": 10}]
            ],
            handle=obj_handle
        )
        fetch_time = time.time() - fetch_start
        print(f"Data fetched in {fetch_time:.2f}s\n")

        pages = data_resp.get("qDataPages", [])
        if pages:
            q_left = pages[0].get("qLeft", [])
            q_data = pages[0].get("qData", [])
            print(f"Received {len(q_left)} left nodes and {len(q_data)} data rows")

            # Check if using tree format
            if q_left:
                first_node = q_left[0]
                if isinstance(first_node, dict) and first_node.get("qSubNodes"):
                    print("Response uses nested tree format (qSubNodes)")
                else:
                    print("Response uses flat/sparse format")

        total_time = time.time() - start_time
        print(f"\nTotal time: {total_time:.2f}s")

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
