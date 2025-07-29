import mysql.connector


def connect(host, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return conn
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

