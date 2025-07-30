import os
from typing import Optional

import aiohttp

from filedgr_lib_ipfs.my_io.my_file_io import build_dir_tree


class IpfsClient:

    def __init__(self, host: str, port: int, protocol: str = "http", **kwargs):
        if host is None and port is None and 'host' not in kwargs and 'port' not in kwargs:
            raise AttributeError("To initialize the IPFS client a hostname/ip and port are required.")
        else:
            self.__host = host
            self.__port = port
            self.__protocol = protocol

    def __get_addr(self):
        return f"{self.__protocol}://{self.__host}:{self.__port}"

    async def ls(self):
        async with aiohttp.ClientSession() as session:
            url = f"{self.__get_addr()}/api/v0/files/ls"
            async with session.post(url=url) as response:
                if response.status == 200:
                    return await response.json()

    async def add_file(self, path: str) -> str:
        if os.path.exists(path) and os.path.isfile(path):
            url = f"{self.__get_addr()}/api/v0/add?cid-version=1"
            files = {
                path: open(path, 'rb')
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, data=files) as resp:
                    if resp.status == 200:
                        return await resp.json()
        else:
            raise FileNotFoundError(f"The file: {path} was not found.")

    async def add_directory(self,
                            path: str,
                            remove_prefix: Optional[str] = None) -> str:
        dirs, files = build_dir_tree(path)
        params = {'pin': 'true'}
        async with aiohttp.ClientSession() as session:
            url = f"{self.__get_addr()}/api/v0/add?cid-version=1"
            with aiohttp.MultipartWriter('form-data') as mpwriter:

                for dir in dirs:
                    if remove_prefix:
                        name = dir.removeprefix(remove_prefix)
                        print(f"removed prefix:{remove_prefix} for dir: {name}")
                    else:
                        name = dir
                        print(f"dir: {name}")
                    folder_part = mpwriter.append(obj='', headers={'content-type': 'application/x-directory'})
                    folder_part.set_content_disposition('form-data', name="file", filename=name)

                for file in files:
                    if remove_prefix:
                        name = file.removeprefix(remove_prefix)
                        print(f"removed prefix:{remove_prefix} for file: {name}")
                    else:
                        name = file
                        print(f"file: {name}")
                    file_part = mpwriter.append(open(file, "rb"))
                    file_part.set_content_disposition('form-data', name="file", filename=name)

                print(f"Calling url: {url}")
                async with session.post(url=url, data=mpwriter, params=params) as resp:
                    if resp.status == 200:
                        import json
                        res = await resp.text()
                        res = res.replace("\n", "")
                        res = res.replace("}{", "},{")
                        res = f"[{res}]"
                        res_dict = json.loads(res)
                        return res_dict
                    else:
                        print(await resp.text())
