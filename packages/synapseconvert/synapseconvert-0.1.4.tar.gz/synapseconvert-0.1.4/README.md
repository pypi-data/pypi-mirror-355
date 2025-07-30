
# synapseconvert

A simple two-way converter for Synapse-style libraries (collections → categories → items) using Excel and JSON. This is intended for developers working with [Synapse](https://substrate.biblicalstory.org/synapse), a research transport protocol designed for structured academic resources.

## 📦 Installation

Install via pip:

```bash
pip install synapseconvert

You’ll then have access to the command-line tools:
	•	synapse-upconvert
	•	synapse-downconvert

🛠 Usage

Convert from Excel to JSON (Upconvert)

synapse-upconvert path/to/input.xlsx path/to/output.json

This reads a spreadsheet and produces a properly nested Synapse metadata file.

Convert from JSON to Excel (Downconvert)

synapse-downconvert path/to/input.json path/to/output.xlsx

This flattens a Synapse-style JSON file into a spreadsheet for editing or review.

📄 Spreadsheet Format

The spreadsheet must contain at least the following columns:
	•	collection – the name of the collection (uniform across all rows)
	•	category – name of the group the item belongs to
	•	title, description, etc. – all other metadata fields are treated as item fields
	•	tags – a valid JSON list (e.g., ["Genesis", "Luke"])

A sample blank spreadsheet is available in this repository as templates -> sample.xlsx

A sample JSON file is available in this repository as templates -> sample.json

🧠 Why This Exists

Synapse is designed to bring remote research libraries directly into Obsidian. Since BiblicalStory cannot make synapse files of all of the repositories that exist, we are providing these tools so that the developers can make synapse libraries of any research library that exists. These libraries can then be added in the synapse settings within Obsidian. 

🔧 Developer Tools

For advanced usage, you can clone this repo and run the commands locally from source:

git clone https://github.com/BiblicalStory/synapseconvert.git
cd synapseconvert
pip install -e .

---


© 2025 BiblicalStory Incorporated. MIT License.

