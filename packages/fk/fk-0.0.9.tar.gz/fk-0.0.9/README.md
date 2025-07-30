
# fk - FactKit: Functional Knowledge for AI

F.K. - FactKit is a lightweight Python package designed for managing and querying simple factual knowledge bases, enabling quick lookup and retrieval of structured data for AI applications. It provides a clean, Pythonic interface, abstracting away the complexities of data storage and manipulation by leveraging powerful existing libraries like `pandas` and `dol`.

## Features

* **Simple Knowledge Representation:** Store facts as structured data (like rows in a table or key-value pairs).
* **Intuitive Interface:** Interact with your knowledge base using standard Python `Mapping` and `MutableMapping` (dictionary-like) behaviors.
* **Flexible Storage Backends:** Easily read and write knowledge from/to local files (JSON, CSV) with extensible support for other storage types via `dol`.
* **Efficient Querying:** Quickly retrieve relevant facts using simple filtering mechanisms powered by `pandas`.
* **Mall for Multi-Store Management:** Organize and access multiple distinct knowledge stores (e.g., "facts", "metadata", "configurations") through a single dictionary-like "mall" object.

## Installation

FactKit can be installed via pip:

```bash
pip install fk 
```

**Dependencies:**
FactKit relies on the following packages, which will be installed automatically:
* `pandas`
* `dol`

## Usage

### 1. The `KnowledgeBase` Object

The core of `fk` is the `KnowledgeBase` class, which behaves like a dictionary:

```python
from fk import KnowledgeBase

# Create an empty knowledge base
kb = KnowledgeBase()

# Add facts (key-value pairs)
kb['apple_info'] = {'name': 'Apple', 'type': 'fruit', 'color': 'red', 'taste': 'sweet'}
kb['banana_info'] = {'name': 'Banana', 'type': 'fruit', 'color': 'yellow', 'taste': 'sweet'}
kb['carrot_info'] = {'name': 'Carrot', 'type': 'vegetable', 'color': 'orange', 'taste': 'earthy'}

# Access facts
print(kb['apple_info'])
# Output: {'name': 'Apple', 'type': 'fruit', 'color': 'red', 'taste': 'sweet'}

# Update a fact
kb['apple_info'] = {'name': 'Apple', 'type': 'fruit', 'color': 'green', 'taste': 'tart'}
print(kb['apple_info'])

# Delete a fact
del kb['banana_info']
print(len(kb)) # Output: 2

# Iterate over keys
for key in kb:
    print(key)

# Querying with filters
fruits = kb.query(filters={'type': 'fruit'})
print(fruits)
# Output: [{'name': 'Apple', 'type': 'fruit', 'color': 'green', 'taste': 'tart'}]

# Get the underlying pandas DataFrame
df = kb.to_dataframe()
print(df)

# Initialize from existing data
initial_data = [
    {'id': 'water', 'element': 'H2O', 'state': 'liquid'},
    {'id': 'oxygen', 'element': 'O2', 'state': 'gas'}
]
kb2 = KnowledgeBase(initial_data)
print(kb2['water'])
```

### 2. File-Based Knowledge Storage (Facade over `dol`)

`fk` provides convenient functions to load and save `KnowledgeBase` objects from/to local files, and a `create_store` function to directly interface with file systems as `MutableMapping` objects.

#### Loading/Saving `KnowledgeBase`

```python
from fk import KnowledgeBase, load_from_csv, save_to_json, save_to_csv, load_from_json
import os

# Example data
data = [
    {'item_id': 1, 'name': 'Laptop', 'category': 'Electronics', 'price': 1200},
    {'item_id': 2, 'name': 'Mouse', 'category': 'Electronics', 'price': 25},
    {'item_id': 3, 'name': 'Keyboard', 'category': 'Electronics', 'price': 75}
]
initial_kb = KnowledgeBase(data)

# Save to JSON
save_to_json(initial_kb, 'my_knowledge.json')
print("Knowledge saved to my_knowledge.json")

# Load from JSON
loaded_kb = load_from_json('my_knowledge.json')
print(loaded_kb.query(filters={'category': 'Electronics'}))

# Save to CSV
save_to_csv(initial_kb, 'my_knowledge.csv', index=False) # index=False to avoid writing pandas index
print("Knowledge saved to my_knowledge.csv")

# Load from CSV (assuming the first column in CSV could be treated as an index)
loaded_kb_csv = load_from_csv('my_knowledge.csv', index_col='item_id') # Specify the index column
print(loaded_kb_csv[1]) # Access by item_id
# Cleanup
os.remove('my_knowledge.json')
os.remove('my_knowledge.csv')
```

#### Direct Store Interface (`create_store`)

For more granular control or when working with individual files as key-value pairs (for JSON), use `create_store`.

```python
from fk import create_store
import os
import shutil

# Create a directory for JSON files
json_dir = './data_json_store'
os.makedirs(json_dir, exist_ok=True)

json_store = create_store(json_dir, format='json')

# Add/retrieve items to the store
json_store['user_123'] = {'name': 'Alice', 'email': 'alice@example.com'}
json_store['product_xyz'] = {'product_name': 'Widget', 'price': 19.99}

print(json_store['user_123'])
# Output: {'name': 'Alice', 'email': 'alice@example.com'}

# List keys in the store
print(list(json_store.keys()))

# Create a directory for CSV (single file mode)
csv_dir = './data_csv_store'
os.makedirs(csv_dir, exist_ok=True)

csv_store = create_store(csv_dir, format='csv')

# Add/retrieve items (these will be stored in a single 'knowledge.csv' file inside csv_dir)
csv_store['fact_1'] = {'subject': 'Earth', 'predicate': 'is', 'object': 'planet'}
csv_store['fact_2'] = {'subject': 'Sun', 'predicate': 'is', 'object': 'star'}
print(csv_store['fact_1'])

# Cleanup
shutil.rmtree(json_dir)
shutil.rmtree(csv_dir)
```

### 3. Managing Multiple Stores with `create_mall`

The `create_mall` function allows you to define and access multiple knowledge stores, each with its own path and format, from a single dictionary.

```python
from fk import create_mall
import os
import shutil

# Define configurations for different stores
mall_configs = {
    'users': {'path': './data/users', 'format': 'json'},
    'products': {'path': './data/products.csv', 'format': 'csv'}, # Specific CSV file
    'configurations': {'path': './data/configs', 'format': 'json'}
}

# Create the mall
my_mall = create_mall(mall_configs)

# Access individual stores through the mall
users_store = my_mall['users']
products_store = my_mall['products']
configs_store = my_mall['configurations']

# Use the stores
users_store['u1'] = {'name': 'Bob', 'role': 'admin'}
products_store['p101'] = {'name': 'Gizmo', 'stock': 150}
configs_store['default_settings'] = {'timeout': 30, 'log_level': 'INFO'}

print(users_store['u1'])
print(products_store['p101'])

# Cleanup
shutil.rmtree('./data')
```

## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---
**Note:** For the `create_store` and `create_mall` functions with `csv` format, especially when treating a *directory* as a CSV store, it will manage a single file named `knowledge.csv` within that directory. If you specify a direct `.csv` file path in the `mall_configs`, it will operate on that specific file. This design choice simplifies the `MutableMapping` facade for CSV, as CSV is inherently a tabular, not key-value, storage.