from __future__ import annotations
from ._credentials import Credentials
from ._io_json import get_json, post_request
import json
import logging

logger = logging.getLogger(__name__)


class ZermeloAPI:

    def __init__(self):
        self.credentials = Credentials()
        self.loaded = False

    async def _init(self, school: str):
        if self.loaded:
            return
        self.zerurl = f"https://{school}.zportal.nl/api/v3/"
        try:
            if not await self.checkCreds():
                with open("creds.ini") as f:
                    token = f.read()
                    await self.add_token(token)
            self.loaded = True
        except Exception as e:
            logger.exception(e)

    async def login(self, code: str) -> bool:
        token = await self.get_access_token(code)
        return await self.add_token(token)

    async def get_access_token(self, code: str) -> str:
        token = ""
        url = self.zerurl + "oauth/token"
        data = {"grant_type": "authorization_code", "code": code}
        response = await post_request(url, data)
        logger.debug(response)
        exit()

        if zerrequest.status_code == 200:
            data = json.loads(zerrequest.text)
            if "access_token" in data:
                token = data["access_token"]
        return token

    async def add_token(self, token: str) -> bool:
        if not token:
            return False
        self.credentials.settoken(token)
        return await self.checkCreds()

    async def checkCreds(self):
        try:
            await self.getName()
            result = True
        except Exception as e:
            logger.error(e)
            result = False
        finally:
            return result

    async def getName(self):
        if not self.credentials.token:
            raise Exception("No Token loaded!")
        status, data = await self.getData("users/~me", True)
        if status != 200 or type(data) is not list:
            raise Exception("could not load user data with token")
        logger.debug(f"get name: {data[0]}")
        row = data[0]
        if not row["prefix"]:
            return " ".join([row["firstName"], row["lastName"]])
        else:
            return " ".join([row["firstName"], row["prefix"], row["lastName"]])

    async def getData(
        self, task, from_id=False
    ) -> tuple[int, list[dict] | str | Exception]:
        result = (500, "unknown error")
        request = (
            self.zerurl + task + f"?access_token={self.credentials.token}"
            if from_id
            else self.zerurl + task + f"&access_token={self.credentials.token}"
        )
        logger.debug(request)
        try:
            data1 = await get_json(request)
            json_response = json.loads(data1.decode("utf-8"))
            if json_response:
                json_status = json_response["response"]["status"]
                if json_status == 200:
                    result = (200, json_response["response"]["data"])
                    logger.debug("    **** JSON OK ****")
                else:
                    logger.debug(f"oeps, geen juiste response: {task}")
                    result = (json_status, json_response["response"])
            else:
                logger.error("JSON - response is leeg")
        except Exception as e:
            logger.exception(e)
            result = (500, e)
        finally:
            return result

    async def load_query(self, query: str) -> list[dict]:
        try:
            status, data = await self.getData(query)
            if status != 200 or type(data) is not list:
                raise Exception(f"Error loading data {status}, {data}")
            if not data:
                logger.debug("no data")
            return data
        except Exception as e:
            logger.debug(e)
            return []


zermelo = ZermeloAPI()


async def loadAPI(name: str) -> ZermeloAPI:
    await zermelo._init(name)
    return zermelo
