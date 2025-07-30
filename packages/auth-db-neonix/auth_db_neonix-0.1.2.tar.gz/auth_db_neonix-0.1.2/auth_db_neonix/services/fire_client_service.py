import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from auth_db_neonix.dto.base_settings_dto import BaseSettingsDto

# TODO utilizzare una transaction per scongiurare problemi di conocorrenza
# TODO verificare che sia safe sui doppioni dei nomi

class FirebaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if not firebase_admin._apps:
            cred_path = Path(__file__).parent / "auth_db_neonix/security/neoquant-config-firebase-adminsdk-fbsvc-a0a678bb10.json"
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)
        self._db = firestore.client()

    @classmethod
    def instance(cls):
        if cls._instance is not None:
            return cls._instance
        else:
            return cls()

    @property
    def db(self):
        return self._db

    @staticmethod
    def create_settings(uid: str, data: BaseSettingsDto):
        def count_function():
            return len(FirebaseClient.load_settings(uid))

        try:
            inst = FirebaseClient.instance()
            idx = count_function()+1
            data["Id"] = idx
            inst.db.collection(uid).document(data["Name"]).create(data)

        except Exception as ex:
            print(ex)

    @staticmethod
    def update_settings(uid: str, data: BaseSettingsDto):
        try:
            inst = FirebaseClient.instance()
            inst.db.collection(uid).document(data["Name"]).update(data)

        except Exception as ex:
            print(ex)

    @staticmethod
    def load_settings(uid: str) -> [dict]:
        try:
            inst = FirebaseClient.instance()
            documents = inst.db.collection(uid).get()
            return [doc.to_dict() for doc in documents if doc.exists]

        except Exception as ex:
            print(ex)

    @staticmethod
    def load_specific_setting(uid: str, name: str) -> dict:
        try:
            inst = FirebaseClient.instance()
            return inst.db.collection(uid).document(name).get().to_dict()

        except Exception as ex:
            print(ex)

