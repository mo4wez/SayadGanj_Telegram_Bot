from peewee import Model, IntegerField, CharField, BooleanField, DateTimeField, SqliteDatabase
import datetime
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(os.path.dirname(current_dir), 'admins.db')
db = SqliteDatabase(db_path)

class Admin(Model):
    """Model for storing admin information"""
    chat_id = IntegerField(unique=True)
    username = CharField(null=True)
    first_name = CharField()
    added_by = IntegerField()  # chat_id of the admin who added this admin
    is_owner = BooleanField(default=False)  # Only one admin can be the owner
    added_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

db.connect()
db.create_tables([Admin], safe=True)