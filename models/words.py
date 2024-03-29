from peewee import Model, SqliteDatabase, CharField, PrimaryKeyField

db = SqliteDatabase(r'C:\Users\moawe\Desktop\sayadganj_bot\db\wordbook.db')

class WordBook(Model):
    _id = PrimaryKeyField()
    betaNoSymbols = CharField()
    betaSymbols = CharField()
    langNoSymbols = CharField()
    langLowercase = CharField()
    langFullWord = CharField()
    entry = CharField()
    soundName = CharField()

    class Meta:
        database = db
        table_name = 'wordbook'

db.connect()