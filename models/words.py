from peewee import Model, SqliteDatabase, CharField, TextField, IntegerField
import os

# Use a relative path based on the current file's location
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(os.path.dirname(current_dir), 'sayadganj.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class SayadGanj(BaseModel):
    id = IntegerField(primary_key=True)
    full_word = CharField()
    full_word_with_symbols = CharField()
    definition = TextField()

    class Meta:
        table_name = 'sayadganj'

# Only connect if the database file exists
if os.path.exists(db_path):
    db.connect()
else:
    print(f"Warning: Database file not found at {db_path}")
    print("Please make sure the sayadganj.db file exists in the project root directory.")