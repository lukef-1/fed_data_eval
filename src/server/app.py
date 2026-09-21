import os
import click

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Date, UniqueConstraint

from datetime import datetime, date


db = SQLAlchemy()


class FREDObservation(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[str] = mapped_column(String(32))
    observation_start: Mapped[date] = mapped_column(Date)
    observation_end: Mapped[date] = mapped_column(Date)
    body: Mapped[str]
    fetched_at: Mapped[datetime] = mapped_column(DateTime)

    __table_args__ = (
        UniqueConstraint("series_id", "observation_start", "observation_end"),
    )


@click.command("init-db")
def init_db():
    db.drop_all()
    db.create_all()
    print("Initialized the database.")


def create_app():
    app = Flask(__name__)
    app.instance_path = os.path.join(app.root_path, "instance")

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    db.init_app(app)
    app.cli.add_command(init_db)

    with app.app_context():
        db.create_all()
        print(db.engine.url)

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    from . import fred

    app.register_blueprint(fred.bp)

    return app
