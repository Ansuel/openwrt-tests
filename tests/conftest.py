import pytest

import pexpect
import sys

def pytest_addoption(parser):
    parser.addoption("--target", action="store", default="x86/64")

class Qemu:
    def __init__(self, pytestconfig):
        self.child = None
        self.pytestconfig = pytestconfig

    def start(self):
        target = "x86"
        subtarget = "64"
        target, subtarget = self.pytestconfig.getoption('target').split("/")
        qemu_cmd = (
            f"./scripts/qemustart {target} {subtarget} --netdev user,id=wan "
            "-netdev user,id=lan,net=192.168.1.0/24,dhcpstart=192.168.1.100,restrict=yes,hostfwd=tcp::8022-:22 "
            "-net nic,netdev=wan -net nic,netdev=lan -device virtio-rng-pci"
        )
        self.child = pexpect.spawn(qemu_cmd, logfile=sys.stdout.buffer)
        self.child.expect("Please press Enter to activate this console.", timeout=80)
        self.child.expect("link becomes ready", timeout=90)
        self.child.send("\n")

    def stop(self):
        self.child.close(force=True)
        self.child = None

    def send_cmd(self, cmd):
        self.child.sendline(cmd)
        self.child.expect(":/#")

    def test_cmd(self, cmd, expect=None):
        self.child.sendline(cmd)
        if expect:
            self.child.expect(expect)
        self.child.expect(":/#")

    def args_parser(self, parser):
        parser.add_argument("target", help="target name")
        parser.add_argument("subtarget", help="subtarget name")

    def args_set(self, args):
        self.args = args


@pytest.fixture
def dut(pytestconfig):
    dut = Qemu(pytestconfig)
    dut.start()
    yield dut
    dut.stop()