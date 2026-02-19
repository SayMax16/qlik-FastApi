#!/usr/bin/env python3
"""Check the object type of UWDJj."""

import sys
sys.path.insert(0, '/Users/saydulloismatov/Documents/qlik sense api/qlik-sense-api')

from src.api.core.config import settings
from src.api.clients.qlik_engine import QlikEngineClient

def main():
    app_id = settings.app_mappings.get("Stock")
    object_id = "UWDJj"

    print(f"Checking object '{object_id}' in app '{app_id}'\n")

    client = QlikEngineClient(settings)
    try:
        client.connect()
        result = client.open_doc(app_id, no_data=False)
        app_handle = result['qReturn']['qHandle']

        # Get object
        obj_resp = client.send_request("GetObject", [object_id], handle=app_handle)
        obj_handle = obj_resp["qReturn"]["qHandle"]

        # Get object info
        obj_info = client.send_request("GetInfo", [], handle=obj_handle)
        obj_type = obj_info.get("qInfo", {}).get("qType", "unknown")
        print(f"Object type: {obj_type}")

        # Get properties
        props = client.send_request("GetProperties", [], handle=obj_handle)
        hc_def = props.get("qProp", {}).get("qHyperCubeDef", {})

        n_dims = len(hc_def.get("qDimensions", []))
        n_meas = len(hc_def.get("qMeasures", []))

        print(f"Dimensions: {n_dims}")
        print(f"Measures: {n_meas}")

        # Print dimension labels
        if n_dims > 0:
            print("\nDimension labels:")
            for d in hc_def.get("qDimensions", []):
                label = d.get("qDef", {}).get("qFieldLabels", [None])[0]
                field = d.get("qDef", {}).get("qFieldDefs", [None])[0]
                print(f"  - {label or field}")

    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
