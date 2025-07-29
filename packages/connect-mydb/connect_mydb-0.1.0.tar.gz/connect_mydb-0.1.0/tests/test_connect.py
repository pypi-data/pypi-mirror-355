from connect_mydb import connect

def test_connection_success():
    db = connect("localhost", "root", "root@123", "test_db")
    assert db is not None
    db.close()

def test_connection_fail():
    db = connect("localhost", "toor", "toor@123", "test_db")
    assert db is None