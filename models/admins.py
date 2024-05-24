from peewee import Model, SqliteDatabase, CharField, PrimaryKeyField

db = SqliteDatabase(r'C:\Users\moawe\Desktop\sayadganj_bot\db\admins.db')

class Admin(Model):
    _id = PrimaryKeyField()
    chat_id = CharField()
    sub_channel = CharField()

    class Meta:
        database = db
        table_name = 'admins'

db.connect()
db.create_tables([Admin], safe=True)