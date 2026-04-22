from pathlib import Path
import os.path
from dataclasses import dataclass
from environs import Env


BASE_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR = BASE_DIR / 'media' / 'video'

matching_entry_points = {
    'start': VIDEO_DIR / 'start_video.mp4',
} # Сопоставление стартового параметра бота и видеоприветствия

video_for_windows = {
    'video_1': VIDEO_DIR / 'video_1.mp4',
    'video_2': VIDEO_DIR / 'video_2.mp4',
    'video_3': VIDEO_DIR / 'video_3.mp4',
    'lighting_1': VIDEO_DIR / 'lighting_1.mp4',
    'lighting_2': VIDEO_DIR / 'lighting_2.mp4',
    'lighting_3': VIDEO_DIR / 'lighting_3.mp4',
    'lighting_4': VIDEO_DIR / 'lighting_4.mp4',
    'lighting_5': VIDEO_DIR / 'lighting_5.mp4',
    'lighting_6': VIDEO_DIR / 'lighting_6.mp4',
    'curtains_1': VIDEO_DIR / 'curtains_1.mp4',
    'climate_1': VIDEO_DIR / 'climate_1.mp4',
    'climate_2': VIDEO_DIR / 'climate_2.mp4',
    'climate_3': VIDEO_DIR / 'climate_3.mp4',
    'climate_4': VIDEO_DIR / 'climate_4.mp4',
    'climate_5': VIDEO_DIR / 'climate_5.mp4',
    'climate_6': VIDEO_DIR / 'climate_6.mp4',
    'leak_1': VIDEO_DIR / 'leak_1.mp4',
    'gates_1': VIDEO_DIR / 'gates_1.mp4',
    'safety_1': VIDEO_DIR / 'safety_1.mp4',
    'safety_2': VIDEO_DIR / 'safety_2.mp4',
    'safety_3': VIDEO_DIR / 'safety_3.mp4',
    'safety_4': VIDEO_DIR / 'safety_4.mp4',
    'saving_1': VIDEO_DIR / 'saving_1.mp4',
    'saving_2': VIDEO_DIR / 'saving_2.mp4',
    'saving_3': VIDEO_DIR / 'saving_3.mp4',

}

# Класс с токеном бота телеграмм
@dataclass
class TgBot:
    token: str  #Токен для доступа к боту


# Класс с объектом TGBot
@dataclass
class Database:
    url: str  # URL подключения к PostgreSQL (async)


@dataclass
class SessionPolicy:
    extension_window_minutes: int
    close_after_last_activity_minutes: int
    sweeper_interval_seconds: int


@dataclass
class Config:
    tg_bot: TgBot
    db: Database
    session_policy: SessionPolicy
    admin: str
    utm_token: str
    webhook_url: str


# Функция создания экземпляра класса config
def load_config(path: str | None = BASE_DIR / '.env'):
    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env("BOT_TOKEN")
        ),
        db=Database(
            url=env("DATABASE_URL")
        ),
        session_policy=SessionPolicy(
            extension_window_minutes=env.int("SESSION_EXTENSION_WINDOW_MINUTES", 4),
            close_after_last_activity_minutes=env.int("SESSION_CLOSE_AFTER_LAST_ACTIVITY_MINUTES", 1),
            sweeper_interval_seconds=env.int("SESSION_SWEEPER_INTERVAL_SECONDS", 60),
        ),
        admin=env("ADMIN_ID"),
        utm_token=env("UTM_TOKEN"),
        webhook_url=env("WEBHOOK_URL"),
    )