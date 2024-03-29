from peewee import Model, SqliteDatabase, CharField

db = SqliteDatabase(r'C:\Users\moawe\Desktop\sayadganj_bot\db\users.db')

class User(Model):
    chat_id = CharField(unique=True)
    first_name = CharField()
    username = CharField(null=True)

    class Meta:
        database = db

db.connect()
db.create_tables([User], safe=True)