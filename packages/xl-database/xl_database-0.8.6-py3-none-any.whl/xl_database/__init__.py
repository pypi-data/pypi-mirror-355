from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, create_engine, func, Table, ForeignKeyConstraint, or_
from sqlalchemy.orm import relationship


class Database(SQLAlchemy):
    def init(self, url):
        engine = create_engine(url)
        metadata = MetaData(bind=engine)
        return engine, metadata

    def mount(self, app):
        super().init_app(app)


db = Database()
session = db.session
