# auth-db-neonix

Authentication and settings management module for Python apps using Firebase for auth and SQLite for local data.

## 🚀 Features

* 🔐 Firebase-based user authentication
* 🔁 Cookie and session management
* 💾 Firebase Firestore settings persistence
* 🗄️ SQLite-based local data layer
* 🧰 Pluggable architecture (DTOs, Services, Models)

## 📦 Installation

### From GitHub

```bash
pip install git+https://github.com/NeoNix-Lab/neoquant-auth-manager.git
```

### For Development

```bash
pip install "git+https://github.com/<your-username>/auth_db_neonix.git#egg=auth_db_neonix[dev]"
```

## 🔧 Usage

```python
from auth_db_neonix import login_user, register_user, DataRetriever

user = register_user("you@example.com", "yourpassword")
cookie = login_user("you@example.com", "yourpassword")

data = DataRetriever.from_settings(user.uid, db_setting)
```

## 🧪 Run Tests

```bash
pytest tests/
```

## 📁 Project Structure

```
.
├── auth_db_neonix/
├── tests/
├── pyproject.toml
├── README.md
├── .gitignore
└── LICENSE
```

## 📄 License

MIT License (see `LICENSE` file)
