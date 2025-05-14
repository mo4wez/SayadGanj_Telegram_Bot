import jdatetime
from peewee import Model, SqliteDatabase, CharField, ForeignKeyField, TextField
import os

# Use a relative path based on the current file's location
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(os.path.dirname(current_dir), 'users.db')
db = SqliteDatabase(db_path)

class User(Model):
    chat_id = CharField(unique=True)
    first_name = CharField()
    username = CharField(null=True)
    start_date = CharField()  # Already included in the model definition

    class Meta:
        database = db

class SearchHistory(Model):
    user = ForeignKeyField(User, backref='searches')
    search_term = TextField()
    search_date = CharField()

    class Meta:
        database = db

# Function to save the user's search
def save_search(chat_id, search_term):
    user, created = User.get_or_create(chat_id=chat_id)
    search_date = jdatetime.datetime.now().strftime("%Y/%m/%d")
    SearchHistory.create(user=user, search_term=search_term, search_date=search_date)

# Remove the add_start_date_column function since start_date is already in the model
# and we're creating the tables from scratch

# Connect to the database
db.connect()

# Create tables if they don't exist
db.create_tables([User, SearchHistory], safe=True)