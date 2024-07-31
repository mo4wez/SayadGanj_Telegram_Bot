from peewee import Model, SqliteDatabase, CharField, DateField, OperationalError
from datetime import datetime

db = SqliteDatabase(r'C:\Users\moawe\Desktop\sayadganj_bot\db\users.db')

class User(Model):
    chat_id = CharField(unique=True)
    first_name = CharField()
    username = CharField(null=True)
    start_date = DateField(default=datetime.now().date)

    class Meta:
        database = db


def add_start_date_column():
    # Raw SQL to add the new column if it doesn't exist
    try:
        db.execute_sql('ALTER TABLE user ADD COLUMN start_date DATE')
    except OperationalError as e:
        if "duplicate column name: start_date" in str(e):
            # The column already exists, ignore the error
            pass
        else:
            raise e
        
db.connect()
add_start_date_column()
db.create_tables([User], safe=True)