from app.database.session import engine

try:
    connection = engine.connect()
    print("DATABASE CONNECTED SUCCESSFULLY")
    connection.close()
except Exception as e:
    print("DATABASE CONNECTION FAILED")
    print(e)