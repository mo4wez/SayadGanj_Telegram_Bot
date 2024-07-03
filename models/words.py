from peewee import Model, SqliteDatabase, CharField, TextField, IntegerField

db = SqliteDatabase(r'C:\Users\moawe\Desktop\sayadganj_bot\db\sayadganj.db')


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

db.connect()