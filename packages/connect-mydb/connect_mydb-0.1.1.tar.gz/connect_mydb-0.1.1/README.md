# connnect_mydb 🔌

A lightweight Python package that helps you connect to a MySQL database with a **single line of code**.

No more boilerplate code — just call `connect()` and you're good to go!

---

## 🚀 Features

- 🔄 One-line MySQL connection
- 🔐 Supports host, user, password, database inputs
- ⚠️ Basic error handling
- 📦 Simple to use and integrate into any project

---

## 📦 Installation

You’ll need `mysql-connector-python`. Install it first:

```bash
pip install mysql-connector-python
```
Then install this package:

```bash
pip install connect-mydb
```

## 💻 Usage

```python
from connect-mydb import connect

try:
    db = connect('localhost', 'root', 'password', 'database_name')
    
    if db:
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        for row in cursor.fetchall():
            print(row)

        cursor.close()
        db.close()

except Exception as e:
    print(f"❌ Error: {e}")

```


## 🙌 Author
Developed by [Mohamed Khasim](https://github.com/k3XD16)


Made with ❤️ for developers who hate repeating themselves.