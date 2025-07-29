import base64
import json
import os
import secrets
import string
from typing import Dict, List, Optional, TypeVar

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

class PoofDocument(BaseModel):
    objId: str = Field(..., alias="_objId", min_length=12, max_length=26)
    data: Dict

    class Config:
        populate_by_name = True

    def __repr__(self):
        return f"PoofDocument(objId={self.objId!r}, data={self.data!r})"

class PoofCollection:
    def __init__(self, name: str):
        self.name = name
        self.documents: Dict[str, PoofDocument] = {}

    @staticmethod
    def generate_obj_id() -> str:
        length = secrets.randbelow(15) + 12
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    async def insert(self, data: T) -> PoofDocument:
        obj_id = self.generate_obj_id()
        while obj_id in self.documents:
            obj_id = self.generate_obj_id()
        document = PoofDocument(objId=obj_id, data=data.dict() if isinstance(data, BaseModel) else data)
        self.documents[obj_id] = document
        return document

    async def find_by_id(self, obj_id: str) -> Optional[PoofDocument]:
        return self.documents.get(obj_id)

    async def find_all(self) -> List[PoofDocument]:
        return list(self.documents.values())

    async def update(self, obj_id: str, data: T) -> Optional[PoofDocument]:
        if obj_id in self.documents:
            document = PoofDocument(objId=obj_id, data=data.dict() if isinstance(data, BaseModel) else data)
            self.documents[obj_id] = document
            return document
        return None

    async def delete(self, obj_id: str) -> bool:
        return bool(self.documents.pop(obj_id, None))

class PoofDatabase:
    def __init__(self, name: str):
        self.name = name
        self.collections: Dict[str, PoofCollection] = {}

    @classmethod
    async def create(cls, name: str) -> 'PoofDatabase':
        if len(name) == 0:
            raise ValueError("Database name cannot be empty")
        return cls(name)

    async def get_collection(self, name: str) -> PoofCollection:
        if name not in self.collections and len(self.collections) < 50:
            self.collections[name] = PoofCollection(name)
        elif name not in self.collections:
            raise ValueError("Maximum number of collections (50) reached")
        return self.collections[name]

class PoofCluster:
    def __init__(self, file_path: str = "cluster.poof", key: Optional[bytes] = None):
        self.file_path = file_path
        self.key = key if key else Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.databases: Dict[str, PoofDatabase] = {}
        self._load()

    @staticmethod
    def _generate_key() -> bytes:
        return Fernet.generate_key()

    def _encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

    def _decrypt(self, data: bytes) -> bytes:
        try:
            return self.cipher.decrypt(data)
        except Exception as e:
            raise ValueError("Decryption failed: invalid key or corrupted data") from e

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f:
                encrypted_data = f.read()
                if encrypted_data:
                    try:
                        data = json.loads(self._decrypt(encrypted_data).decode())
                        for db_name, collections in data.items():
                            db = PoofDatabase(db_name)
                            for coll_name, docs in collections.items():
                                coll = PoofCollection(coll_name)
                                for doc in docs:
                                    coll.documents[doc["_objId"]] = PoofDocument(objId=doc["_objId"], data=doc["data"])
                                db.collections[coll_name] = coll
                            self.databases[db_name] = db
                    except Exception as e:
                        raise ValueError("Failed to load cluster: invalid key or corrupted data") from e

    async def save(self):
        data = {}
        for db_name, db in self.databases.items():
            data[db_name] = {}
            for coll_name, coll in db.collections.items():
                data[db_name][coll_name] = [doc.dict(by_alias=True) for doc in coll.documents.values()]
        encrypted_data = self._encrypt(json.dumps(data).encode())
        with open(self.file_path, "wb") as f:
            f.write(encrypted_data)

    @classmethod
    async def create(cls, file_path: str = "cluster.poof", key: Optional[str] = None) -> 'PoofCluster':
        key_bytes = base64.b64decode(key) if key else None
        return cls(file_path, key_bytes)

    async def get_database(self, name: str) -> PoofDatabase:
        if name not in self.databases and len(self.databases) < 10:
            self.databases[name] = await PoofDatabase.create(name)
        elif name not in self.databases:
            raise ValueError("Maximum number of databases (10) reached")
        return self.databases[name]

    def get_encryption_key(self) -> str:
        return base64.b64encode(self.key).decode()