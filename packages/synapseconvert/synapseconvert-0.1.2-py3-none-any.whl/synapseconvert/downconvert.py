import json
import pandas as pd
import sys

input_path = sys.argv[1] if len(sys.argv) > 1 else "metadata.json"
output_path = sys.argv[2] if len(sys.argv) > 2 else "synapse_library.xlsx"

with open(input_path, "r") as f:
    data = json.load(f)

collection = data["Collection"]["name"]
rows = []
for category in data["Collection"]["Categories"]:
    for item in category["items"]:
        rows.append({
            "collection": collection,
            "category": category["name"],
            **item
        })

df = pd.DataFrame(rows)
df.to_excel(output_path, index=False)
print(f"✅ Downconverted {input_path} to {output_path}")
