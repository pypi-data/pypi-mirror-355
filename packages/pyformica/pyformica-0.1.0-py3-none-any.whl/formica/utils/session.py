import contextlib
from functools import wraps
from inspect import signature
from typing import Any
from typing import AsyncGenerator
from typing import Awaitable
from typing import Callable
from typing import cast
from typing import ParamSpec
from typing import TypeVar

from formica.settings import engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.ext.asyncio.session import AsyncSession as SASession

SessionLocal = async_sessionmaker(bind=engine, class_=SASession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[Any, Any]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@contextlib.asynccontextmanager
async def _create_session() -> AsyncGenerator[AsyncSession, None]:
    """Contextmanager that will create and teardown a session."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


PS = ParamSpec("PS")
RT = TypeVar("RT")


def find_session_idx(func: Callable[PS, RT]) -> int:
    """Find the index of the 'session' parameter in the function signature."""
    func_params = signature(func).parameters
    try:
        return tuple(func_params).index("session")
    except ValueError:
        raise ValueError(
            f"Function {func.__qualname__} has no 'session' parameter"
        ) from None


def provide_session(func: Callable[PS, Awaitable[RT]]) -> Callable[PS, Awaitable[RT]]:
    """
    Async decorator to provide a session to a coroutine if not provided.
    """
    session_args_idx = find_session_idx(func)

    @wraps(func)
    async def wrapper(*args, **kwargs) -> RT:
        if "session" in kwargs or session_args_idx < len(args):
            return await func(*args, **kwargs)
        else:
            async with _create_session() as session:
                return await func(*args, session=session, **kwargs)

    return wrapper


# A fake session to use in functions decorated by provide_session. This allows
# the 'session' argument to be of type Session instead of Session | None,
# making it easier to type hint the function body without dealing with the None
# case that can never happen at runtime.
NEW_SESSION: SASession = cast(SASession, None)
