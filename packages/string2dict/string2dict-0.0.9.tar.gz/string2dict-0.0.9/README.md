# String2Dict

`string2dict` is a Python library designed to transform complex strings into Python dictionaries. It is particularly useful when working with text-based outputs from language models (LLMs) that need to be parsed into valid JSON objects or Python dictionaries. This class provides functionality for cleaning, sanitizing, and parsing such text data 
efficiently.

Since LLMs often return data with extra characters, formatting inconsistencies, or embedded code markers, it can be challenging to directly parse the output into JSON or dictionaries. `String2Dict` aims to simplify this process by handling common formatting issues and providing a robust parsing mechanism.

## Key Features

- **Strips Whitespace**: Removes unnecessary leading and trailing whitespace from strings.
- **Removes Embedded Markers**: Cleans code markers like ```json``` or ``` to ensure the string is ready for parsing.
- **Ensures Valid JSON Braces**: Adjusts strings to ensure they start and end with curly braces (`{}`).
- **Supports JSON and Python Parsing**: Tries to parse strings using `json.loads` first, and falls back to `ast.literal_eval` if needed.
- **Handles Multiple Dictionaries**: Extracts and parses multiple dictionary-like strings from a single input.

## Installation & Usage

To use `String2Dict`: 

```
pip install string2dict 
```

```python
from string2dict import String2Dict
s2d=String2Dict()
llm_output = "```json\n{\"name\": \"ChatGPT\", \"version\": \"4.0\"}\n```"
parsed_dict= s2d.run(llm_output)
print(parsed_dict)

```

**Output:**
```
{'name': 'ChatGPT', 'version': '4.0'}
```


### Example 2: Parsing Multiple Dictionaries from a String

```python
# Input string containing multiple dictionaries
llm_output = """
```json
{"name": "ChatGPT", "version": "4.0"}
{"name": "GPT-3", "version": "3.0"}
```"""

# Extract and convert each dictionary into a list of dictionaries
parsed_dicts = s2d.string_to_dict_list(llm_output)
print(parsed_dicts)
```

**Output:**

```
[
    {'name': 'ChatGPT', 'version': '4.0'},
    {'name': 'GPT-3', 'version': '3.0'}
]
```


## Methods

### 1. `strip_surrounding_whitespace(string: str) -> str`
   - Strips leading and trailing whitespace from the input string.
   - **Args**: `string` (str) - The input string.
   - **Returns**: Stripped string.

### 2. `remove_embedded_markers(string: str) -> str`
   - Removes embedded markers like ```json``` and other code block markers.
   - **Args**: `string` (str) - The input string.
   - **Returns**: Cleaned string.

### 3. `ensure_string_starts_and_ends_with_braces(string: str) -> str`
   - Ensures the string starts and ends with curly braces (`{}`).
   - **Args**: `string` (str) - The input string.
   - **Returns**: Adjusted string.

### 4. `parse_as_json(string: str) -> dict`
   - Attempts to parse the string as JSON using `json.loads`.
   - **Args**: `string` (str) - The input JSON string.
   - **Returns**: Parsed dictionary.

### 5. `parse_with_literal_eval(string: str) -> dict`
   - Attempts to parse the string using Python's `ast.literal_eval`.
   - **Args**: `string` (str) - The input string.
   - **Returns**: Parsed dictionary.

### 6. `run(string: str) -> dict`
   - Processes a string through all cleaning and parsing steps, returning a parsed dictionary.
   - **Args**: `string` (str) - The input string.
   - **Returns**: Parsed dictionary or `None` if parsing fails.

### 7. `string_to_dict_list(string: str) -> list`
   - Extracts multiple dictionaries from a string and converts each to a Python dictionary.
   - **Args**: `string` (str) - The input string containing one or more dictionaries.
   - **Returns**: A list of parsed dictionaries, or `None` if parsing fails.

## Logging

The `String2Dict` class supports logging for easier debugging. Set the `debug` parameter to `True` when initializing the class to enable detailed logging.

## Error Handling

The class handles parsing errors gracefully:
- If `json.loads` fails, it attempts to use `ast.literal_eval`.
- If both methods fail, it logs an error and returns `None`.
