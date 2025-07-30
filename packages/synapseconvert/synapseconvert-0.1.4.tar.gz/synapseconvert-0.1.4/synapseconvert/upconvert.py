import pandas as pd
import json
import sys


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "synapse_library.xlsx"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "metadata.json"

    df = pd.read_excel(input_path)
    collection_name = df["collection"].iloc[0]
    categories = {}

    for _, row in df.iterrows():
        cat = row["category"]
        item = row.drop(["collection", "category"]).dropna().to_dict()
        if isinstance(item.get("tags"), str):
            try:
                item["tags"] = json.loads(item["tags"].replace("'", '"'))
            except:
                item["tags"] = []
        categories.setdefault(cat, []).append(item)

    collection = {
        "Collection": {
            "name": collection_name,
            "designator": "BST",
            "url": "https://thebiblicalstory.org",
            "Categories": [{"name": k, "items": v} for k, v in categories.items()]
        }
    }

    with open(output_path, "w") as f:
        json.dump(collection, f, indent=2)

    print(f"✅ Upconverted {input_path} to {output_path}")


if __name__ == "__main__":
    main()
