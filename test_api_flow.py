#!/usr/bin/env python3
"""Test the EXACT flow that the API uses."""

import sys
sys.path.insert(0, '/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api')

from src.api.core.config import settings
from src.api.clients.qlik_engine import QlikEngineClient
import time

def main():
    app_id = settings.app_mappings.get("Stock")
    object_id = "5f78a4f8-3ea6-40b2-8ed8-9eeef2bf9e21"
    bookmark_id = "0ff80188-58b9-4684-8d72-2b7efe1ee395"

    print("Testing EXACT API flow from get_pivot_data()")
    print("=" * 60)

    client = QlikEngineClient(settings)
    try:
        # Step 1: Connect and open app (like app_repository line 340)
        print("\n1. Connecting and opening app...")
        start = time.time()
        client.connect()
        result = client.open_doc(app_id, no_data=False)
        app_handle = result['qReturn']['qHandle']
        print(f"   Done in {time.time() - start:.2f}s, app_handle={app_handle}")

        # Step 2: Apply bookmark FIRST (like get_pivot_data line 1160)
        print(f"\n2. Applying bookmark '{bookmark_id}'...")
        start = time.time()
        apply_result = client.apply_bookmark(app_handle, bookmark_id)
        print(f"   Done in {time.time() - start:.2f}s, success={apply_result}")

        # Step 3: GetObject (like get_pivot_data line 1167)
        print(f"\n3. Getting object '{object_id}'...")
        start = time.time()
        obj_resp = client.send_request("GetObject", [object_id], handle=app_handle)
        obj_handle = obj_resp["qReturn"]["qHandle"]
        print(f"   Done in {time.time() - start:.2f}s, obj_handle={obj_handle}")

        # Step 4: GetProperties (like get_pivot_data line 1171)
        print("\n4. Getting properties...")
        start = time.time()
        props = client.send_request("GetProperties", [], handle=obj_handle)
        props_time = time.time() - start
        print(f"   Done in {props_time:.2f}s")

        hc_def = props.get("qProp", {}).get("qHyperCubeDef", {})
        n_dims = len(hc_def.get("qDimensions", []))
        n_meas = len(hc_def.get("qMeasures", []))
        print(f"   Dimensions: {n_dims}, Measures: {n_meas}")

        # Step 5: GetLayout (like get_pivot_data line 1191) - THIS IS SLOW IN API!
        print("\n5. Getting layout (THIS IS SLOW IN API - 127s)...")
        start = time.time()
        layout = client.send_request("GetLayout", [], handle=obj_handle)
        layout_time = time.time() - start
        print(f"   Done in {layout_time:.2f}s")

        hc = layout.get("qLayout", {}).get("qHyperCube", {})
        total_rows = hc.get("qSize", {}).get("qcy", 0)
        print(f"   Total rows: {total_rows}")

        # Step 6: GetHyperCubePivotData (like get_pivot_data line 1220)
        print("\n6. Getting pivot data (10 rows)...")
        start = time.time()
        data_resp = client.send_request(
            "GetHyperCubePivotData",
            [
                "/qHyperCubeDef",
                [{"qLeft": 0, "qTop": 0, "qWidth": max(n_meas, 1), "qHeight": 10}]
            ],
            handle=obj_handle
        )
        print(f"   Done in {time.time() - start:.2f}s")

        pages = data_resp.get("qDataPages", [])
        if pages:
            q_left = pages[0].get("qLeft", [])
            q_data = pages[0].get("qData", [])
            print(f"   Received {len(q_left)} left nodes, {len(q_data)} data rows")

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
