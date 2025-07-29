"""Module for working with Juke Audio device"""

import aiohttp
import base64
import json

from .exceptions import AuthenticationException, UnexpectedException
from typing import List

api_version = "v2"

import logging
logger = logging.getLogger(__name__)

def create_auth_header(user_name: str, password: str):
    """Return auth header value"""
    return base64.b64encode(bytes(f"{user_name}:{password}", "utf-8")).decode("utf-8")


def is_juke_compatible(ver: str):
    """Create auth header value"""
    return ver.startswith(f"{api_version}.")


class JukeAudioClient:
    """Class for working with Juke Audio device"""
    async def can_connect_to_juke(self, ip_address: str):
        """Verify connectivity to a compatible Juke device"""
        logger.debug(f"Verifying connectivity to Juke with ip_address={ip_address}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{ip_address}/api/") as response:
                    try:
                        contents = await response.json(content_type=None)
                        return is_juke_compatible(contents["versions"][0])
                    except:
                        ### Juke currently is not returning JSON from the current API so we need to parse it manually
                        contents = await response.text()
                        contents = contents.replace("'", "\"")
                        versions = json.loads(contents)
                        for ver in versions:
                            if is_juke_compatible(ver):
                                return True

        except Exception as exc:
            logger.error(f"Error connecting to Juke device: {exc}")
            return False


    async def get_devices(self, ip_address: str, username: str, password: str) -> List[str]:
        """Get device list"""
        logger.debug(f"Invoking get_devices with ip_address={ip_address}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/devices/") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting devices: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc
        
    async def get_device_connection_info(self, ip_address: str, username: str, password: str, device_id: str):
        """Get connection information"""
        logger.debug(f"Invoking get_device_connection_info with ip_address={ip_address}, device_id={device_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/devices/{device_id}/connection") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting device connection info: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_device_attributes(self, ip_address: str, username: str, password: str, device_id: str):
        """Get device attributes"""
        logger.debug(f"Invoking get_device_attributes with ip_address={ip_address}, device_id={device_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/devices/{device_id}/attributes") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting device attributes: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_device_config(self, ip_address: str, username: str, password: str, device_id: str):
        """Get device config"""
        logger.debug(f"Invoking get_device_config with ip_address={ip_address}, device_id={device_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/devices/{device_id}/config") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting device config: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_device_metrics(self, ip_address: str, username: str, password: str, device_id: str):
        """Get device metrics"""
        logger.debug(f"Invoking get_device_metrics with ip_address={ip_address}, device_id={device_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/devices/{device_id}/metrics") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting device metrics: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_zones(self, ip_address: str, username: str, password: str):
        """Get zone ids"""
        logger.debug(f"Invoking get_zones with ip_address={ip_address}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/zones") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting zones: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_zone_config(self, ip_address: str, username: str, password: str, zone_id: str):
        """Get zone config"""
        logger.debug(f"Invoking get_zone_config with ip_address={ip_address}, zone_id={zone_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/zones/{zone_id}") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting zone config: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc
        
    async def set_zone_volume(self, ip_address: str, username: str, password: str, zone_id: str, volume: int):
        """Set zone volume"""
        logger.debug(f"Invoking set_zone_volume with ip_address={ip_address}, zone_id={zone_id}, volume={volume}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.put(f"http://{ip_address}/api/{api_version}/zones/{zone_id}/volume", data = { "volume": volume}) as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error setting zone volume: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.text()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def set_zone_input(self, ip_address: str, username: str, password: str, zone_id: str, input: str):
        """Set zone input"""
        logger.debug(f"Invoking set_zone_input with ip_address={ip_address}, zone_id={zone_id}, input={input}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            data = "[]"
            if input is not None and len(input)>0:
                data = f"[\"{input}\"]"

            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.put(f"http://{ip_address}/api/{api_version}/zones/{zone_id}/input", data = data) as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error setting zone input: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.text()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_inputs(self, ip_address: str, username: str, password: str):
        """Get input ids"""
        logger.debug(f"Invoking get_inputs with ip_address={ip_address}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/inputs") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting inputs: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_input_config(self, ip_address: str, username: str, password: str, input_id: str):
        """Get input config"""
        logger.debug(f"Invoking get_input_config with ip_address={ip_address}, input_id={input_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/inputs/{input_id}") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting input config: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc
        
    async def get_available_inputs(self, ip_address: str, username: str, password: str, input_id: str):
        """Get available inputs"""
        logger.debug(f"Invoking get_available_inputs with ip_address={ip_address}, input_id={input_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/inputs/{input_id}/available-types") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting available inputs: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents["available_types"]
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def get_input_types(self, ip_address: str, username: str, password: str, input_id: str):
        """Get input types"""
        logger.debug(f"Invoking get_input_types with ip_address={ip_address}, input_id={input_id}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.get(f"http://{ip_address}/api/{api_version}/inputs/{input_id}/types") as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error getting input types: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.json()
                        return contents["available_types"]
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def set_input_type(self, ip_address: str, username: str, password: str, input_id: str, type: str):
        """Set input type"""
        logger.debug(f"Invoking set_input_type with ip_address={ip_address}, input_id={input_id}, type={type}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}

            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.put(f"http://{ip_address}/api/{api_version}/inputs/{input_id}/type", data =  { "type": type }) as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error setting input type: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.text()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def set_input_volume(self, ip_address: str, username: str, password: str, input_id: str, volume: int):
        """Set input volume"""
        logger.debug(f"Invoking set_input_volume with ip_address={ip_address}, input_id={input_id}, volume={volume}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}
            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.put(f"http://{ip_address}/api/{api_version}/inputs/{input_id}/volume", data = { "volume": volume}) as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error setting zone volume: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.text()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc

    async def enable_input(self, ip_address: str, username: str, password: str, input_id: str, enable: bool):
        """Enable/disable an input"""
        logger.debug(f"Invoking enable_input with ip_address={ip_address}, input_id={input_id}, enable={enable}")
        try:
            hdr = {"Authorization": f"Bearer {create_auth_header(username, password)}"}

            async with aiohttp.ClientSession(headers=hdr) as session:
                async with session.put(f"http://{ip_address}/api/{api_version}/inputs/{input_id}/enable", data =  { "enable": enable }) as response:
                    if response.status != 200:
                        if response.status == 401 or response.status == 403:
                            logger.error(f"Authentication error: {response.status}")
                            raise AuthenticationException
                        else:
                            logger.error(f"Error enabling/disabling input: {response.status}")
                            raise UnexpectedException(response.status)
                    else:
                        contents = await response.text()
                        return contents
        except aiohttp.ClientError as exc:
            raise UnexpectedException from exc