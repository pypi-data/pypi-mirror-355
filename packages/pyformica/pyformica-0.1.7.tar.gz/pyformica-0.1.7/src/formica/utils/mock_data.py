import asyncio
import json
import logging
import multiprocessing

import aiohttp
from formica import settings
from formica.models.constant import ConnectionType
from formica.models.constant import DeviceType
from formica.models.constant import UserRole
from formica.models.models import CredentialModel
from formica.models.models import DeviceModel
from formica.models.models import DeviceSetModel
from formica.models.models import GroupModel
from formica.models.models import User
from formica.utils.session import NEW_SESSION
from formica.utils.session import provide_session
from formica.web.main import run_webserver
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)


async def start_api_server() -> multiprocessing.Process:
    process = multiprocessing.Process(target=run_webserver, args=[7999], daemon=False)
    print("Staring API server in as a daemon...")
    process.start()

    # Wait for the server to start?
    await asyncio.sleep(10)
    return process


def get_groups_data() -> dict:
    with open(
        "src/formica/utils/mock_data/mock_data.json", "r", encoding="utf-8"
    ) as file:
        return json.load(file)


def get_users_data() -> dict:
    with open(
        "src/formica/utils/mock_data/mock_users.json", "r", encoding="utf-8"
    ) as file:
        return json.load(file)


@provide_session
async def insert_users(users_mock_data: dict, session: AsyncSession = NEW_SESSION):
    async with aiohttp.ClientSession() as aiohttp_session:
        for user in users_mock_data["users"]:
            payload = {
                "email": user["email"],
                "name": user["name"],
                "password": user["password"],
            }
            async with aiohttp_session.post(
                "http://localhost:8000/api/auth/register", json=payload
            ) as response:
                if response.status == 201:
                    print(f"User {user['name']} created successfully.")
                else:
                    print(f"Failed to create user {user['name']}.")

    # Manually fix the is_active and is_superuser fields
    for user in users_mock_data["users"]:
        user_db: User = await User.get_user_by_email(user["email"], session=session)
        user_db.is_active = user["is_active"]
        user_db.is_superuser = user["is_superuser"]
        user_db.role = UserRole(user["role"])

    await session.commit()


@provide_session
async def insert_groups(groups_mock_data: dict, session: AsyncSession = NEW_SESSION):
    for group in groups_mock_data["groups"]:
        # Insert the groups
        group_db = GroupModel(
            group_id=group["group_id"], description=group["description"]
        )
        session.add(group_db)

        # Add the members for the groups
        group_db = await session.get(GroupModel, group["group_id"])
        members_to_add = await User.get_user_by_emails(
            group["members"], session=session
        )
        for member in members_to_add:
            group_db.members.append(member)

        # Insert the devices
        for device in group["devices"]:
            device_db = DeviceModel(
                device_id=device["device_id"],
                device_type=DeviceType(device["device_type"]),
                group_id=group["group_id"],
                ip=device["ip"],
            )
            session.add(device_db)

            # Insert the credentials of devices
            for credential in device["credentials"]:
                credential["connection_type"] = ConnectionType(
                    credential["connection_type"]
                )
                credential["group_id"] = group["group_id"]
                device_db.credentials.append(CredentialModel(**credential))

        # Create the device sets
        for device_set in group["device_sets"]:
            device_set_db = DeviceSetModel(
                device_set_id=device_set["device_set_id"],
                description=device_set["description"],
                group_id=group["group_id"],
            )
            session.add(device_set_db)
            for dev_id in device_set["devices"]:
                device_set_db.devices.append(
                    await DeviceModel.get_by_key(
                        group["group_id"], dev_id, session=session
                    )
                )

    await session.commit()


async def insert_flows_data(users_mock_data, session: AsyncSession = NEW_SESSION):
    async with aiohttp.ClientSession() as aiohttp_session:
        for user in users_mock_data["users"]:
            # Login
            form = aiohttp.FormData()
            form.add_field("username", user["email"])
            form.add_field("password", user["password"])

            async with aiohttp_session.post(
                "http://localhost:8000/api/auth/jwt/login", data=form
            ) as response:
                token = (await response.json())["access_token"]

            if not token:
                print(f"Failed to login user {user['name']}.")
                continue

            headers = {"Authorization": f"Bearer {token}"}

            # Creat the flows
            for flow in user["flows"]:
                await insert_flows(aiohttp_session, flow, headers)

    await session.commit()


async def insert_flows(aiohttp_session, flow, headers):
    payload = {
        "flow_id": flow["flow_id"],
        "description": flow["description"],
        "group_id": flow["group_id"],
    }
    async with aiohttp_session.post(
        "http://localhost:8000/api/flows", headers=headers, json=payload
    ) as response:
        print(await response.text())
        if response.status == 201:
            print(f"Flow {flow['flow_id']} created successfully.")
            for version in flow["flow_versions"]:
                await insert_flow_versions(aiohttp_session, flow, version, headers)
        else:
            print(f"Failed to create flow {flow['flow_id']}.")


async def insert_flow_versions(aiohttp_session, flow, flow_version, headers):
    payload = {
        "flow_id": flow["flow_id"],
        "version": flow_version["version"],
        "structure": flow_version["structure"],
        "parameters": flow_version["parameters"],
    }
    async with aiohttp_session.post(
        "http://localhost:8000/api/flow-versions",
        headers=headers,
        json=payload,
    ) as response:
        if response.status == 201:
            print(f"Flow version {flow_version['version']} created successfully.")
            # for flow_run in flow_version["flow_runs"]:
            #     await insert_flow_runs(
            #         aiohttp_session, flow, flow_version, flow_run, headers
            #     )
        else:
            print(f"Failed to create flow version {flow_version['version']}.")


async def insert_flow_runs(aiohttp_session, flow, flow_version, flow_run, headers):
    payload = {
        "flow_id": flow["flow_id"],
        "version": flow_version["version"],
        "description": flow_version["description"],
        "device_set_id": flow_run["device_set_id"],
        "run_type": flow_run["run_type"],
    }
    async with aiohttp_session.post(
        "http://localhost:8000/api/flow-runs",
        headers=headers,
        json=payload,
    ) as response:
        if response.status == 201:
            print("Flow run created successfully.")
        else:
            print("Failed to create flow run.")


@provide_session
async def insert_mock_data(session: AsyncSession = NEW_SESSION):
    groups_mock_data = get_groups_data()
    users_mock_data = get_users_data()

    # Start the api server so that we can register user
    # api_server_process = await start_api_server()
    await insert_users(users_mock_data, session)
    # api_server_process.terminate()

    await insert_groups(groups_mock_data, session)
    await insert_flows_data(users_mock_data, session)


async def clear_all_tables():
    async with settings.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def main():
    # await clear_all_tables()
    await insert_mock_data()


if __name__ == "__main__":
    asyncio.run(main())
