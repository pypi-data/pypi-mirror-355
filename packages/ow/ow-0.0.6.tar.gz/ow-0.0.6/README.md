# ow
functions that work on soup

To install:	```pip install ow```

## Overview
The `ow` package provides a collection of utilities designed to facilitate the manipulation and querying of HTML/XML structures using BeautifulSoup. It includes functions to navigate through the structure, extract information, and even open HTML content in a web browser for debugging or inspection purposes.

## Features
- **Navigational Utilities**: Traverse through the HTML tree structure to find parent elements or specific paths.
- **HTML Content Handling**: Save HTML tags to a file and view them in Firefox, aiding in debugging and visualization.
- **Data Extraction**: Simplify the extraction of text from specified tags and automatically apply text transformations.
- **Batch Element Retrieval**: Retrieve multiple elements based on complex path specifications, supporting both simple and nested queries.

## Installation
Install the package using pip:
```bash
pip install ow
```

## Usage Examples

### Finding the Root Parent of a Tag
To find the root parent of a BeautifulSoup tag:
```python
from bs4 import BeautifulSoup
from ow import root_parent

soup = BeautifulSoup("<div><span>Example</span></div>", "html.parser")
span_tag = soup.find('span')
root = root_parent(span_tag)
print(root)  # Outputs the div tag
```

### Open a Tag in Firefox
To open a tag's HTML content in Firefox for debugging:
```python
from bs4 import BeautifulSoup
from ow import open_tag_in_firefox

soup = BeautifulSoup('<div><span>Open me in Firefox</span></div>', 'html.parser')
span_tag = soup.find('span')
open_tag_in_firefox(span_tag)
```

### Adding Text to a Parse Dictionary
Extract text from a specified tag and add it to a dictionary, optionally applying a text transformation:
```python
from bs4 import BeautifulSoup
from ow import add_text_to_parse_dict

soup = BeautifulSoup('<div><p id="para"> Some text </p></div>', 'html.parser')
parse_dict = {}
add_text_to_parse_dict(soup, parse_dict, key='paragraph', name='p', attrs={'id': 'para'}, text_transform=str.strip)
print(parse_dict)  # Outputs: {'paragraph': 'Some text'}
```

### Getting Elements by Path
Retrieve elements from a BeautifulSoup object by specifying a path:
```python
from bs4 import BeautifulSoup
from ow import get_elements

soup = BeautifulSoup('<div><p>First</p><p>Second</p></div>', 'html.parser')
elements = get_elements(soup, ['p'])
print([e.text for e in elements])  # Outputs: ['First', 'Second']
```

## Function Documentation

### `root_parent(s)`
Returns the furthest ancestor of a BeautifulSoup tag.

### `open_tag_in_firefox(tag)`
Saves the HTML of a BeautifulSoup tag to a temporary file and opens it in Firefox.

### `add_text_to_parse_dict(soup, parse_dict, key, name, attrs, text_transform)`
Finds a tag in the given BeautifulSoup object `soup` by `name` and `attrs`, extracts its text, applies a `text_transform` function, and adds it to `parse_dict` under `key`.

### `get_element(node, path_to_element)`
Retrieves an element from a BeautifulSoup node by following a specified path. The path can be a string, list, or dictionary describing how to find the element.

### `get_elements(nodes, path_to_element)`
Recursively retrieves elements from a node or list of nodes in a BeautifulSoup object by following a list of paths. Each path can be a string, list, or dictionary that specifies how to find the elements.

## Contributing
Contributions to the `ow` package are welcome. Please ensure that any pull requests or issues are detailed with examples and expected outcomes.