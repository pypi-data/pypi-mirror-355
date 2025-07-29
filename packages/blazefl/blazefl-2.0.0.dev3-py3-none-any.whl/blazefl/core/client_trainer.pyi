from multiprocessing.pool import ApplyResult as ApplyResult
from pathlib import Path
from typing import Protocol, TypeVar

UplinkPackage = TypeVar('UplinkPackage')
DownlinkPackage = TypeVar('DownlinkPackage', contravariant=True)

class BaseClientTrainer(Protocol[UplinkPackage, DownlinkPackage]):
    def uplink_package(self) -> list[UplinkPackage]: ...
    def local_process(self, payload: DownlinkPackage, cid_list: list[int]) -> None: ...
DiskSharedData = TypeVar('DiskSharedData', covariant=True)

class ProcessPoolClientTrainer(BaseClientTrainer[UplinkPackage, DownlinkPackage], Protocol[UplinkPackage, DownlinkPackage, DiskSharedData]):
    num_parallels: int
    share_dir: Path
    device: str
    device_count: int
    cache: list[UplinkPackage]
    def get_shared_data(self, cid: int, payload: DownlinkPackage) -> DiskSharedData: ...
    def get_client_device(self, cid: int) -> str: ...
    @staticmethod
    def process_client(path: Path, device: str) -> Path: ...
    def local_process(self, payload: DownlinkPackage, cid_list: list[int]) -> None: ...

class ThreadPoolClientTrainer(BaseClientTrainer[UplinkPackage, DownlinkPackage], Protocol[UplinkPackage, DownlinkPackage]):
    num_parallels: int
    device: str
    device_count: int
    cache: list[UplinkPackage]
    def process_client(self, cid: int, device: str, payload: DownlinkPackage) -> UplinkPackage: ...
    def get_client_device(self, cid: int) -> str: ...
    def local_process(self, payload: DownlinkPackage, cid_list: list[int]) -> None: ...
