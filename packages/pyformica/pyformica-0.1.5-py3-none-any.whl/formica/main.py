import asyncio
import logging
import multiprocessing
import signal
import sys
from functools import partial
from multiprocessing import Process

import typer
from formica import settings
from formica.executor.executor import LocalExecutor
from formica.scheduler.scheduler import Scheduler
from formica.settings import app_config
from formica.web.main import run_webserver
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)
app = typer.Typer()


def handle_signal(webserver_process: Process, signum, frame):
    logger.info(f"\nReceived signal {signum}, exiting gracefully...")
    webserver_process.terminate()
    sys.exit(0)


@app.command()
def webserver():
    print("HELLO, STARTING WEB SERVER")
    run_webserver()


@app.command()
def scheduler():
    asyncio.run(_scheduler())


async def _scheduler():
    scheduler_ = Scheduler(LocalExecutor())
    await scheduler_.run()


async def _init():
    print("initializing database...")
    settings.init()
    print("database initialized")
    async with settings.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@app.command()
def init():
    """Khởi tạo thư mục dữ liệu ở đường dẫn `FORMICA_HOME.
    Lệnh này phải được chạy trước tiên để có thể chạy được các thành phần khác"""
    asyncio.run(_init())


@app.command()
def standalone():
    init()

    # Chạy Webserver
    process = multiprocessing.Process(target=webserver, daemon=False)
    print("Staring API server in as a daemon...")
    logger.info("Staring API server as a daemon...")

    for sig in {signal.SIGINT, signal.SIGTERM}:
        signal.signal(sig, partial(handle_signal, process))

    process.start()
    scheduler()


def main():
    # multiprocessing.set_start_method("spawn")
    # logging.basicConfig()
    app()


if __name__ == "__main__":
    main()
