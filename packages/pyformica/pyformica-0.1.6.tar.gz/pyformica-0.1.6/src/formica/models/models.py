import uuid
from datetime import datetime
from typing import Optional

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users.db import SQLAlchemyUserDatabase
from formica.models.constant import ConnectionType
from formica.models.constant import DeviceRunState
from formica.models.constant import DeviceType
from formica.models.constant import FlowRunState
from formica.models.constant import FlowRunType
from formica.models.constant import INITIAL_FLOW_STATE
from formica.models.constant import TaskState
from formica.models.constant import TaskTriggerRule
from formica.models.constant import UserRole
from formica.models.request_models import CredentialFilters
from formica.models.request_models import DeviceFilters
from formica.models.request_models import DeviceSetFilters
from formica.models.request_models import FlowFilters
from formica.models.request_models import FlowRunFilters
from formica.models.request_models import FlowVersionFilters
from formica.models.request_models import GroupFilters
from formica.utils.session import get_session
from formica.utils.session import NEW_SESSION
from formica.utils.session import provide_session
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import func
from sqlalchemy import JSON
from sqlalchemy import Select
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlmodel import desc
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import select
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

Base = declarative_base(metadata=SQLModel.metadata)
UUID_ID = uuid.UUID


# Junction table for many-to-many relationship
class UserGroupLink(SQLModel, table=True):
    __tablename__ = "user_group_link"
    email: str = Field(foreign_key="user.email", primary_key=True, ondelete="CASCADE")
    group_id: str = Field(
        foreign_key="user_group.group_id", primary_key=True, ondelete="CASCADE"
    )


class User(SQLAlchemyBaseUserTableUUID, Base):
    name = Column(String)
    role = Column(Enum(UserRole))
    groups: list["GroupModel"] = Relationship(
        back_populates="members", link_model=UserGroupLink
    )
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    @classmethod
    @provide_session
    async def get_all(cls, session: AsyncSession = Depends(get_session)):
        stmt: Select = select(User)
        return (await session.exec(stmt)).unique().all()

    @provide_session
    async def get_group_ids(self, session: AsyncSession = Depends(get_session)):
        stmt: Select = select(UserGroupLink.group_id).where(
            UserGroupLink.email == self.email
        )
        return (await session.exec(stmt)).all()

    @classmethod
    @provide_session
    async def get_user_by_email(cls, email: str, session: AsyncSession = NEW_SESSION):
        stmt: Select = select(User).where(User.email == email)
        return (await session.exec(stmt)).first()

    @classmethod
    @provide_session
    async def get_user_by_ids(
        cls, user_ids: list[str], session: AsyncSession = NEW_SESSION
    ):
        stmt: Select = select(User).where(User.id.in_(user_ids))
        return (await session.exec(stmt)).all()

    @classmethod
    @provide_session
    async def get_user_by_emails(
        cls, emails: list[str], session: AsyncSession = NEW_SESSION
    ):
        stmt: Select = select(User).where(User.email.in_(emails))
        return (await session.exec(stmt)).all()


async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)


class GroupModel(SQLModel, table=True):
    __tablename__ = "user_group"
    group_id: str = Field(primary_key=True)
    description: str = Field(default="")

    devices: list["DeviceModel"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    device_sets: list["DeviceSetModel"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    flows: list["FlowModel"] = Relationship(back_populates="group")
    members: list[User] = Relationship(
        link_model=UserGroupLink, sa_relationship_kwargs={"lazy": "joined"}
    )

    @classmethod
    @provide_session
    async def filter(
        cls, user: User, filters: GroupFilters, session: AsyncSession = NEW_SESSION
    ) -> list["GroupModel"]:
        query: Select = select(GroupModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(DeviceModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        group_ids = await user.get_group_ids(session)

        if not user.is_superuser:
            query = query.where(GroupModel.group_id.in_(group_ids))

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def get_all(cls, session: AsyncSession = Depends(get_session)):
        stmt: Select = select(GroupModel)
        return (await session.exec(stmt)).unique().all()

    @provide_session
    async def add_members(
        self, members: list[User], session: AsyncSession = NEW_SESSION
    ):
        for member in members:
            stmt: Select = select(UserGroupLink).where(
                UserGroupLink.id == member.id,
                UserGroupLink.group_id == self.group_id,
            )
            if not (await session.exec(stmt)).first():
                user_group_link = UserGroupLink(id=member.id, group_id=self.group_id)
                session.add(user_group_link)

    @classmethod
    @provide_session
    async def get_members(cls, group, session: AsyncSession = NEW_SESSION):
        stmt: Select = (
            select(User)
            .join(UserGroupLink)
            .where(UserGroupLink.group_id == group.group_id)
        )
        return (await session.exec(stmt)).all()

    @classmethod
    @provide_session
    async def group_existed(
        cls, group_id: str, session: AsyncSession = NEW_SESSION
    ) -> bool:
        return (await GroupModel.get_by_key(group_id, session)) is not None

    @classmethod
    @provide_session
    async def get_by_key(
        cls, group_id: str, session: AsyncSession = NEW_SESSION
    ) -> Optional["GroupModel"]:
        return await session.get(GroupModel, group_id)


class FlowModel(SQLModel, table=True):
    __tablename__ = "flow"
    flow_id: str = Field(default="", primary_key=True)
    owner_id: UUID_ID = Field(foreign_key="user.id")
    group_id: str = Field(foreign_key="user_group.group_id")
    saved_state: dict = Field(sa_column=Column(JSON), default=INITIAL_FLOW_STATE)
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)

    group: GroupModel = Relationship(
        back_populates="flows", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    @provide_session
    async def filter(
        cls, user: User, filters: FlowFilters, session: AsyncSession = NEW_SESSION
    ):
        query: Select = select(FlowModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(DeviceModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        if not user.is_superuser:
            query = query.where(
                FlowModel.group_id.in_(await user.get_group_ids(session))
            )

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def flow_existed(
        cls, flow_id: str, session: AsyncSession = NEW_SESSION
    ) -> bool:
        return (await FlowModel.get_by_key(flow_id, session)) is not None

    @classmethod
    @provide_session
    async def get_by_key(cls, flow_id: str, session: AsyncSession = NEW_SESSION):
        return await session.get(FlowModel, flow_id)

    @classmethod
    @provide_session
    async def get_all(cls, session: AsyncSession = NEW_SESSION):
        stmt: Select = select(FlowModel)
        return (await session.exec(stmt)).unique().all()


class FlowVersionModel(SQLModel, table=True):
    __tablename__ = "flow_version"
    flow_id: str = Field(primary_key=True, foreign_key="flow.flow_id")
    version: str = Field(primary_key=True)
    parameters: list[str] = Field(sa_column=Column(JSON))
    structure: dict = Field(sa_column=Column(JSON))
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)

    flow: FlowModel = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    @classmethod
    @provide_session
    async def filter(
        cls,
        user: User,
        filters: FlowVersionFilters,
        session: AsyncSession = NEW_SESSION,
    ):
        query: Select = select(FlowVersionModel).join(FlowModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(FlowVersionModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        if not user.is_superuser:
            query = query.where(
                FlowModel.group_id.in_(await user.get_group_ids(session))
            )

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def flow_version_existed(
        cls, flow_id: str, version: str, session: AsyncSession = NEW_SESSION
    ) -> bool:
        return (
            await FlowVersionModel.get_by_key(flow_id, version, session)
        ) is not None

    @classmethod
    @provide_session
    async def get_by_key(
        cls, flow_id: str, version: str, session: AsyncSession = NEW_SESSION
    ):
        return await session.get(FlowVersionModel, (flow_id, version))


class FlowRunModel(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ["flow_id", "version"],
            ["flow_version.flow_id", "flow_version.version"],
        ),
    )
    __tablename__ = "flow_run"
    flow_id: str = Field(primary_key=True)
    version: str = Field(primary_key=True)
    flow_run_id: str = Field(primary_key=True)
    owner_id: UUID_ID = Field(foreign_key="user.id")
    description: str = Field(default="")
    device_set_id: str = Field(foreign_key="device_set.device_set_id")
    args: Optional[dict[str, str]] = Field(sa_column=Column(JSON))
    run_type: FlowRunType = Field(sa_column=Column(Enum(FlowRunType)))
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = Field()
    state: FlowRunState = Field(default=FlowRunState.SUBMITTED)
    created_at: datetime = Field(default_factory=datetime.now)

    device_runs: list["DeviceRunModel"] = Relationship(
        back_populates="flow_run",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    flow_version: FlowVersionModel = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    @provide_session
    async def filter(
        cls,
        user: User,
        filters: FlowRunFilters,
        session: AsyncSession = NEW_SESSION,
    ):
        query: Select = select(FlowRunModel).join(FlowVersionModel).join(FlowModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(FlowRunModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        if not user.is_superuser:
            query = query.where(
                FlowModel.group_id.in_(await user.get_group_ids(session))
            ).where(FlowRunModel.owner_id == user.id)

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def flow_run_existed(
        cls,
        flow_id: str,
        version: str,
        flow_run_id: str,
        session: AsyncSession = NEW_SESSION,
    ) -> bool:
        return (
            await FlowRunModel.get_by_key(flow_id, version, flow_run_id, session)
        ) is not None

    @classmethod
    @provide_session
    async def get_by_key(
        cls,
        flow_id: str,
        version: str,
        flow_run_id: str,
        session: AsyncSession = NEW_SESSION,
    ):
        return await session.get(FlowRunModel, (flow_id, version, flow_run_id))

    @classmethod
    @provide_session
    async def get_flowrun_to_schedule(cls, session: AsyncSession = NEW_SESSION):
        """Lấy các FlowRun có trạng thái SUBMITTED hoặc RUNNING để schedule"""
        stmt: Select = select(FlowRunModel).where(
            (FlowRunModel.state == FlowRunState.SUBMITTED)
            | (FlowRunModel.state == FlowRunState.RUNNING)
        )
        return (await session.exec(stmt)).all()

    def set_state(self, new_state: FlowRunState):
        if new_state == FlowRunState.SUBMITTED:
            raise ValueError("Can't set a FlowRun's state to SUBMITTED")
        elif new_state == FlowRunState.RUNNING:
            self.start_time = datetime.now()
            self.state = new_state
        elif new_state == FlowRunState.FINISHED:
            self.end_time = datetime.now()
            self.state = new_state
        else:
            raise ValueError(f"Invalid FlowRunState: {new_state}")


# Junction table for many-to-many relationship
class DeviceSetLink(SQLModel, table=True):
    __tablename__ = "device_set_link"

    device_id: str = Field(foreign_key="device.device_id", primary_key=True)
    device_set_id: str = Field(foreign_key="device_set.device_set_id", primary_key=True)


class DeviceModel(SQLModel, table=True):
    __tablename__ = "device"
    group_id: str = Field(primary_key=True, foreign_key="user_group.group_id")
    device_id: str = Field(primary_key=True)
    device_type: DeviceType = Field()
    ip: str = Field()

    group: GroupModel = Relationship(back_populates="devices")
    device_sets: list["DeviceSetModel"] = Relationship(
        back_populates="devices", link_model=DeviceSetLink
    )
    credentials: list["CredentialModel"] = Relationship(
        back_populates="device",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )

    @classmethod
    @provide_session
    async def filter(
        cls, user: User, filters: DeviceFilters, session: AsyncSession = NEW_SESSION
    ):
        query: Select = select(DeviceModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(DeviceModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        if not user.is_superuser:
            query = query.where(
                DeviceModel.group_id.in_(await user.get_group_ids(session))
            )

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def get_devices_by_id(
        cls, device_ids: list[str], session: AsyncSession = NEW_SESSION
    ):
        stmt: Select = select(DeviceModel).where(DeviceModel.device_id.in_(device_ids))
        return (await session.exec(stmt)).all()

    @classmethod
    @provide_session
    async def get_all(cls, session: AsyncSession = NEW_SESSION):
        stmt: Select = select(DeviceModel)
        return (await session.exec(stmt)).unique().all()

    @classmethod
    @provide_session
    async def device_existed(
        cls, group_id: str, dev_id: str, session: AsyncSession = NEW_SESSION
    ) -> bool:
        return (await DeviceModel.get_by_key(group_id, dev_id, session)) is not None

    @classmethod
    @provide_session
    async def get_by_key(
        cls, group_id: str, dev_id: str, session: AsyncSession = NEW_SESSION
    ):
        return await session.get(DeviceModel, (group_id, dev_id))


class DeviceSetModel(SQLModel, table=True):
    __tablename__ = "device_set"
    device_set_id: str = Field(primary_key=True)
    description: str = Field(default="")
    group_id: str = Field(foreign_key="user_group.group_id")

    devices: list[DeviceModel] = Relationship(
        back_populates="device_sets",
        link_model=DeviceSetLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    group: GroupModel = Relationship(back_populates="device_sets")

    @classmethod
    @provide_session
    async def filter(
        cls, user: User, filters: DeviceSetFilters, session: AsyncSession = NEW_SESSION
    ):
        query: Select = select(DeviceSetModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(DeviceSetModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        if not user.is_superuser:
            query = query.where(
                DeviceSetModel.group_id.in_(await user.get_group_ids(session))
            )

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def get_by_key(cls, device_set_id: str, session: AsyncSession = NEW_SESSION):
        return await session.get(DeviceSetModel, device_set_id)

    @classmethod
    @provide_session
    async def get_all(cls, session: AsyncSession = NEW_SESSION):
        stmt: Select = select(DeviceSetModel)
        return (await session.exec(stmt)).unique().all()


class CredentialModel(SQLModel, table=True):
    __tablename__ = "credential"

    __table_args__ = (
        UniqueConstraint("group_id", "device_id", "connection_type", "priority"),
    )

    id: Optional[int] = Field(primary_key=True)
    device_id: str = Field(foreign_key="device.device_id")
    group_id: str = Field(foreign_key="user_group.group_id")
    connection_type: ConnectionType = Field()
    priority: int = Field()
    description: str = Field()
    username: str = Field()
    password: Optional[str] = Field()
    port: int = Field()
    extra: dict = Field(sa_column=Column(JSON))

    device: DeviceModel = Relationship(
        back_populates="credentials", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    @provide_session
    async def filter(
        cls, user: User, filters: CredentialFilters, session: AsyncSession = NEW_SESSION
    ):
        query: Select = select(CredentialModel).join(DeviceModel)

        for field_name, value in filters.model_dump(exclude_none=True).items():
            column = getattr(DeviceModel, field_name)
            query = query.where(column == value)
            print(f"{column} = {value}")

        if not user.is_superuser:
            query = query.where(
                DeviceModel.group_id.in_(await user.get_group_ids(session))
            )

        return (await session.exec(query)).unique().all()

    @classmethod
    @provide_session
    async def get_all(cls, session: AsyncSession = Depends(get_session)):
        stmt: Select = select(CredentialModel)
        return (await session.exec(stmt)).unique().all()

    @classmethod
    @provide_session
    async def credential_existed(
        cls,
        group_id: str,
        device_id: str,
        connection_type: ConnectionType,
        priority: int,
        session: AsyncSession = Depends(get_session),
    ):
        stmt: Select = select(CredentialModel).where(
            CredentialModel.group_id == group_id,
            CredentialModel.device_id == device_id,
            CredentialModel.connection_type == connection_type,
            CredentialModel.priority == priority,
        )
        return (await session.exec(stmt)).first() is not None

    @classmethod
    @provide_session
    async def get_by_key(cls, credential_id: str, session: AsyncSession = NEW_SESSION):
        return await session.get(CredentialModel, credential_id)


class DeviceRunModel(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ["flow_id", "version", "flow_run_id"],
            ["flow_run.flow_id", "flow_run.version", "flow_run.flow_run_id"],
        ),
    )
    __tablename__ = "device_run"
    device_run_db_id: Optional[int] = Field(primary_key=True)
    flow_id: str = Field()
    version: str = Field()
    flow_run_id: str = Field()
    device_id: str = Field(foreign_key="device.device_id")
    state: DeviceRunState = Field(default=DeviceRunState.QUEUED)
    logical_start_time: datetime = Field()
    actual_start_time: Optional[datetime] = Field()
    end_time: Optional[datetime] = Field()
    created_at: datetime = Field(default_factory=datetime.now)

    device: DeviceModel = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
    flow_run: FlowRunModel = Relationship(
        back_populates="device_runs", sa_relationship_kwargs={"lazy": "selectin"}
    )
    tasks: list["TaskModel"] = Relationship(
        back_populates="device_run", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    @provide_session
    async def get_latest_device_run_of_flowrun(
        cls, flowrun: FlowRunModel, session: AsyncSession = NEW_SESSION
    ):
        stmt: Select = (
            select(DeviceRunModel)
            .where(
                (DeviceRunModel.flow_id == flowrun.flow_id)
                & (DeviceRunModel.version == flowrun.version)
                & (DeviceRunModel.flow_run_id == flowrun.flow_run_id)
            )
            .order_by(desc(DeviceRunModel.actual_start_time))
        )
        return (await session.exec(stmt)).first()

    def set_state(self, new_state: DeviceRunState):
        if new_state == DeviceRunState.QUEUED:
            raise ValueError("Can't set a DeviceRun's state to QUEUED")
        elif new_state == DeviceRunState.RUNNING:
            self.state = new_state
            self.actual_start_time = datetime.now()
        elif new_state in (DeviceRunState.SUCCESS, DeviceRunState.FAILED):
            self.state = new_state
            self.end_time = datetime.now()
        else:
            raise ValueError(f"Invalid DeviceRunState: {new_state}")


class TaskModel(SQLModel, table=True):
    __tablename__ = "task"
    device_run_db_id: str = Field(
        primary_key=True, foreign_key="device_run.device_run_db_id"
    )
    node_id: str = Field(primary_key=True)
    state: TaskState = Field(default=TaskState.WAIT_FOR_EXECUTING)
    trigger_rule: TaskTriggerRule = Field(default=TaskTriggerRule.SUCCESS)
    created_at: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = Field()
    end_time: Optional[datetime] = Field()

    device_run: DeviceRunModel = Relationship(back_populates="tasks")

    @classmethod
    @provide_session
    async def get_tasks_by_flow_and_run_id(
        cls, flow_id: str, run_id: str, session: AsyncSession = NEW_SESSION
    ):
        stmt: Select = select(TaskModel).where(
            TaskModel.flow_id == flow_id and TaskModel.run_id == run_id
        )
        return (await session.exec(stmt)).all()

    def set_state(self, new_state: TaskState):
        if new_state == TaskState.WAIT_FOR_EXECUTING:
            raise ValueError("Can't set a Task's state to WAIT_FOR_EXECUTING")
        elif new_state == TaskState.RUNNING:
            self.state = new_state
            self.start_time = datetime.now()
        elif new_state in (TaskState.SUCCESS, TaskState.FAILED):
            self.state = new_state
            self.end_time = datetime.now()
        elif new_state == TaskState.SKIPPED:
            self.state = new_state
            self.start_time = None
            self.end_time = None
        else:
            raise ValueError(f"Invalid TaskState: {new_state}")
