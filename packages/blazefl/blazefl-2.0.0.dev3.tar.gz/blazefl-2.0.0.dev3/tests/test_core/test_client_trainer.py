from dataclasses import dataclass
from pathlib import Path

import pytest
import torch

from src.blazefl.core import ProcessPoolClientTrainer


@dataclass
class UplinkPackage:
    cid: int
    message: str


@dataclass
class DownlinkPackage:
    message: str


@dataclass
class DiskSharedData:
    cid: int
    payload: DownlinkPackage


class DummyProcessPoolClientTrainer(
    ProcessPoolClientTrainer[UplinkPackage, DownlinkPackage, DiskSharedData]
):
    def __init__(self, num_parallels: int, share_dir: Path, device: str):
        self.num_parallels = num_parallels
        self.share_dir = share_dir
        self.share_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        if self.device == "cuda":
            self.device_count = torch.cuda.device_count()
        self.cache: list[UplinkPackage] = []

    def uplink_package(self) -> list[UplinkPackage]:
        return self.cache

    def get_shared_data(self, cid: int, payload: DownlinkPackage) -> DiskSharedData:
        return DiskSharedData(cid=cid, payload=payload)

    @staticmethod
    def process_client(path: Path, device: str) -> Path:
        data = torch.load(path, weights_only=False)
        _ = device
        downlink_package = data.payload

        dummy_uplink_package = UplinkPackage(
            cid=data.cid, message=downlink_package.message + "<client_to_server>"
        )

        torch.save(dummy_uplink_package, path)
        return path


@pytest.mark.parametrize("num_parallels", [1, 2, 4])
@pytest.mark.parametrize("cid_list", [[], [42], [0, 1, 2]])
def test_process_pool_client_trainer(
    tmp_path: Path, num_parallels: int, cid_list: list[int]
) -> None:
    trainer = DummyProcessPoolClientTrainer(
        num_parallels=num_parallels, share_dir=tmp_path, device="cpu"
    )

    dummy_payload = DownlinkPackage(message="<server_to_client>")

    trainer.local_process(dummy_payload, cid_list)

    assert len(trainer.cache) == len(cid_list)
    for i, cid in enumerate(cid_list):
        result = trainer.cache[i]
        assert result.cid == cid
        assert result.message == "<server_to_client><client_to_server>"

    package = trainer.uplink_package()
    assert len(package) == len(cid_list)

    for i, cid in enumerate(cid_list):
        result = package[i]
        assert result.cid == cid
        assert result.message == "<server_to_client><client_to_server>"
