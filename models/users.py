import jdatetime
from peewee import Model, SqliteDatabase, CharField, OperationalError, ForeignKeyField, TextField

db = SqliteDatabase(r'C:\Users\moawe\Desktop\sayadganj_bot\db\users.db')

class User(Model):
    chat_id = CharField(unique=True)
    first_name = CharField()
    username = CharField(null=True)
    start_date = CharField()

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
db.create_tables([User, SearchHistory], safe=True)