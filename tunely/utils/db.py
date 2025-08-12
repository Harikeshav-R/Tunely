import logging
import os

from datetime import datetime, UTC
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from tunely.utils.config import Config
from tunely.utils.constants import Constants

_logger = logging.getLogger(__name__)

Base = declarative_base()


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, nullable=False)
    credentials = Column(String, nullable=False)
    type = Column(String, nullable=False)


class DownloadedSong(Base):
    __tablename__ = 'downloaded_songs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(String, nullable=False)
    download_path = Column(String, nullable=False)
    time = Column(DateTime, default=datetime.now(UTC), nullable=False)

    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    account = relationship("Account", back_populates="downloaded_songs")

    @property
    def path(self) -> Path:
        return Path(self.download_path)

    @path.setter
    def path(self, value: Path):
        self.download_path = str(value)


class Database:
    os.makedirs(Constants.CONFIG_DEFAULT_DATABASE_DIR, exist_ok=True)
    _engine = create_engine(f"sqlite://{Config.get("database", "db_file")}", echo=True)
    Base.metadata.create_all(_engine)

    _Session = sessionmaker(bind=_engine)
    _session = _Session()

    @classmethod
    def create_account(cls, user_name: str, credentials: str, type_: str):
        new_account = Account(user_name=user_name, credentials=credentials, type=type_)
        cls._session.add(new_account)
        cls._session.commit()

        _logger.info(f"Created new account: [{user_name}]")

    @classmethod
    def get_account_by_id(cls, account_id: int) -> Account | None:
        _logger.debug(f"Getting account by ID: {account_id}")
        return cls._session.query(Account).filter(Account.id == account_id).first()

    @classmethod
    def get_account_by_user_name(cls, user_name: str) -> Account | None:
        _logger.debug(f"Getting account by user name: {user_name}")
        return cls._session.query(Account).filter(Account.user_name == user_name).first()

    @classmethod
    def get_accounts(cls) -> list[type[Account]]:
        _logger.debug("Getting all accounts")
        return cls._session.query(Account).all()

    @classmethod
    def update_account(cls, account: Account):
        _logger.debug(f"Updating account: {account}")
        cls._session.add(account)
        cls._session.commit()

    @classmethod
    def delete_account(cls, account: Account):
        _logger.debug(f"Deleting account: {account}")
        cls._session.delete(account)
        cls._session.commit()

    @classmethod
    def create_downloaded_song(cls, song_id: str, account: Account, path: str):
        _logger.info(f"Creating new downloaded song: {song_id}")

        new_downloaded_song = DownloadedSong(song_id=song_id, download_path=path, account_id=account.id)
        cls._session.add(new_downloaded_song)
        cls._session.commit()

    @classmethod
    def get_downloaded_songs_by_account(cls, account: Account) -> list[type[DownloadedSong]]:
        _logger.debug(f"Getting downloaded songs by account: {account}")

        return cls._session.query(DownloadedSong).filter(DownloadedSong.account_id == account.id).all()

    @classmethod
    def get_downloaded_songs_by_id(cls, song_id: str) -> DownloadedSong | None:
        _logger.debug(f"Getting downloaded song by ID: {song_id}")

        return cls._session.query(DownloadedSong).filter(DownloadedSong.song_id == song_id).first()

    @classmethod
    def get_downloaded_songs(cls) -> list[type[DownloadedSong]]:
        _logger.debug("Getting all downloaded songs")

        return cls._session.query(DownloadedSong).all()

    @classmethod
    def update_downloaded_song(cls, song: DownloadedSong):
        _logger.debug(f"Updating downloaded song: {song}")

        cls._session.add(song)
        cls._session.commit()

    @classmethod
    def delete_downloaded_song(cls, song: DownloadedSong):
        _logger.debug(f"Deleting downloaded song: {song}")

        cls._session.delete(song)
        cls._session.commit()
