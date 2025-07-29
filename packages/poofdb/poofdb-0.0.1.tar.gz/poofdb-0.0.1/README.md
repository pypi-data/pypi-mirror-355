# PoofDB

PoofDB is a lightweight, file-based, encrypted NoSQL database for Python, built with Pydantic for data validation and Fernet for encryption. It supports asynchronous operations, allowing you to store and manage structured data in a simple JSON-like format with strong encryption.

## Features
- **Encrypted Storage**: All data is encrypted using Fernet (symmetric encryption) with a user-provided or auto-generated key.
- **Pydantic Integration**: Validates data using Pydantic models for type safety and structure.
- **Asynchronous API**: Built for async applications using Python's `asyncio`.
- **Simple Structure**: Organizes data into databases (max 10), collections (max 50 per database), and documents with unique IDs (12–26 characters).
- **File-Based**: Stores data in a single encrypted file (e.g., `cluster.poof`).

## Quick Start
Create a simple script to use PoofDB. Below is an example (`simple_db.py`) that inserts and reads a document using a custom Pydantic model.

```python
import asyncio
from pydantic import BaseModel
from poof import PoofCluster

class User(BaseModel):
    name: str
    age: int

async def main():
    # Use an existing key or generate a new one (see "Generating a New Key")
    key = "your key"
    
    # Create cluster
    cluster = await PoofCluster.create("cluster.poof", key=key)
    
    # Get database and collection
    db = await cluster.get_database("my_db")
    coll = await db.get_collection("my_collection")
    
    # Insert document
    user = User(name="Alice", age=25)
    doc = await coll.insert(user)
    print(f"Inserted: objId={doc.objId}, Name={user.name}, Age={user.age}")
    
    # Read document
    found_doc = await coll.find_by_id(doc.objId)
    if found_doc:
        user_data = User(**found_doc.data)
        print(f"Found: objId={found_doc.objId}, Name={user_data.name}, Age={user_data.name}")
    
    # Save cluster
    await cluster.save()

if __name__ == "__main__":
    asyncio.run(main())
```

Run the script:
```bash
python simple_db.py
```

**Output**:
```
Inserted: objId=XyZ123AbCdEfGhIjKlMnOp, Name=Alice, Age=25
Found: objId=XyZ123AbCdEfGhIjKlMnOp, Name=Alice, Age=25
```

## Generating a New Key
To create a new cluster with a new encryption key, use the following script (`new_cluster_key.py`):

```python
import asyncio
from poof import PoofCluster

async def main():
    cluster = await PoofCluster.create("new_cluster.poof")
    key = cluster.get_encryption_key()
    print(f"New encryption key: {key}")
    await cluster.save()
    print(f"New cluster created at: new_cluster.poof")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python new_cluster_key.py
```

**Output**:
```
New encryption key: a1B2c3D4e5F6g7H8i9J0kL1mN2oP3qR4sT5uV6wX7yZ8=
New cluster created at: new_cluster.poof
```

**Important**: Save the key securely, as it’s required to access the cluster file. Lost keys cannot be recovered.

## API Overview
- **PoofCluster**: Manages the database file and encryption.
  - `create(file_path, key=None)`: Creates or loads a cluster.
  - `get_encryption_key()`: Returns the base64-encoded key.
  - `get_database(name)`: Retrieves or creates a database.
  - `save()`: Saves the cluster to the file.
- **PoofDatabase**: Manages collections (max 50).
  - `get_collection(name)`: Retrieves or creates a collection.
- **PoofCollection**: Manages documents.
  - `insert(data)`: Inserts a document with a random ID (12–26 chars).
  - `find_by_id(obj_id)`: Finds a document by ID.
  - `find_all()`: Returns all documents.
  - `update(obj_id, data)`: Updates a document.
  - `delete(obj_id)`: Deletes a document.
- **PoofDocument**: Represents a document with an `objId` and `data` (dictionary).

## Custom Models
Define your own Pydantic model to validate data. For example:

```python
class MyModel(BaseModel):
    field1: str
    field2: int
```

Use it in place of `User` in the example above.

## Limitations
- Maximum 10 databases per cluster.
- Maximum 50 collections per database.
- Document IDs are 12–26 characters, randomly generated.
- Data is stored in a single file, which may not scale for very large datasets.
- Encryption key must be managed manually.

## Error Handling
- **Invalid Key**: Raises `ValueError: Decryption failed` if the key is incorrect.
- **Validation Errors**: Pydantic raises `ValidationError` if data doesn’t match the model.
- **Limits Exceeded**: Raises `ValueError` if database or collection limits are reached.