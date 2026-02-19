#!/usr/bin/env python3
"""Find the correct object for application_status table."""

import sys
sys.path.insert(0, '/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api')

from src.api.core.config import settings
from src.api.clients.qlik_engine import QlikEngineClient

def main():
    app_id = settings.app_mappings.get("Stock")
    print(f"Searching for application_status object in Stock app: {app_id}\n")

    client = QlikEngineClient(settings)
    try:
        client.connect()
        result = client.open_doc(app_id, no_data=True)
        app_handle = result['qReturn']['qHandle']

        # Get ALL objects (not just pivot-table)
        all_infos_result = client.send_request("GetAllInfos", [], handle=app_handle)
        all_objects = all_infos_result.get("qInfos", [])

        print(f"Found {len(all_objects)} total objects in the app\n")
        print("=" * 80)

        # Look for objects with "application" or "status" in the ID
        # or check the original object ID from .env
        original_id = "TyZkPXB"

        candidates = []
        for obj in all_objects:
            obj_id = obj.get("qId", "")
            obj_type = obj.get("qType", "")

            # Check if this is the original ID or contains relevant keywords
            is_candidate = (
                obj_id == original_id or
                "application" in obj_id.lower() or
                "status" in obj_id.lower() or
                obj_type in ["pivot-table", "table", "qlik-table"]
            )

            if is_candidate:
                candidates.append(obj)
                print(f"CANDIDATE: ID={obj_id}, Type={obj_type}")

                # Try to get more info about this object
                if obj_id == original_id:
                    print(f"    ^^^ THIS IS THE ORIGINAL .env OBJECT ID ^^^")
                print()

        print("=" * 80)
        print(f"\nFound {len(candidates)} candidate objects")

        # Now let's inspect each candidate more closely
        print("\n" + "=" * 80)
        print("DETAILED INSPECTION:")
        print("=" * 80 + "\n")

        for obj in candidates:
            obj_id = obj.get("qId", "")
            obj_type = obj.get("qType", "")

            print(f"\nObject ID: {obj_id}")
            print(f"Type: {obj_type}")

            try:
                # Get the object
                obj_resp = client.get_object(app_handle, obj_id)
                obj_handle = obj_resp["qReturn"]["qHandle"]

                # Get layout to see the actual data structure
                layout = client.send_request("GetLayout", [], handle=obj_handle)

                qLayout = layout.get("qLayout", {})
                qMeta = qLayout.get("qMeta", {})
                title = qMeta.get("title", "No title")

                print(f"Title: {title}")

                # Check if it has a hypercube
                if "qHyperCube" in qLayout:
                    hc = qLayout["qHyperCube"]
                    dims = hc.get("qDimensionInfo", [])
                    meas = hc.get("qMeasureInfo", [])

                    print(f"Dimensions ({len(dims)}):")
                    for d in dims[:5]:  # Show first 5
                        print(f"  - {d.get('qFallbackTitle', 'N/A')}")
                    if len(dims) > 5:
                        print(f"  ... and {len(dims) - 5} more")

                    print(f"Measures ({len(meas)}):")
                    for m in meas[:5]:  # Show first 5
                        print(f"  - {m.get('qFallbackTitle', 'N/A')}")
                    if len(meas) > 5:
                        print(f"  ... and {len(meas) - 5} more")

                    # Check if dimension/measure names suggest this is application_status
                    all_labels = [d.get('qFallbackTitle', '') for d in dims] + [m.get('qFallbackTitle', '') for m in meas]
                    if any('application' in str(l).lower() or 'status' in str(l).lower() or 'заявк' in str(l).lower() for l in all_labels):
                        print("\n    >>> LIKELY application_status table (has application/status/заявка fields) <<<")

                print("-" * 80)

            except Exception as e:
                print(f"Could not get details: {e}")
                print("-" * 80)

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
