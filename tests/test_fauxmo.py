"""test_fauxmo.py :: Tests for `fauxmo` package."""

import json
import socket
import xml.etree.ElementTree as etree

from fauxmo import fauxmo
from fauxmo.plugins.simplehttpplugin import SimpleHTTPPlugin

import pytest
import requests


def test_udp_search(fauxmo_server: pytest.fixture) -> None:
    """Test device search request to UPnP / SSDP server"""

    msg = b'"ssdp:discover"' + b'urn:Belkin:device:**'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(msg, ('localhost', 1900))
    data = sock.recv(4096)

    assert b'LOCATION: http://' in data
    assert b'/setup.xml' in data


def test_setup(fauxmo_server: pytest.fixture) -> None:
    """Test TCP server's `/setup.xml` endpoint"""

    r = requests.get('http://127.0.0.1:12345/setup.xml')
    assert r.status_code == 200

    root = etree.fromstring(r.text)
    assert root.find(".//friendlyName").text == 'fake switch one'


def test_turnon(fauxmo_server: pytest.fixture,
                simplehttpplugin_target: pytest.fixture) -> None:
    """Test TCP server's "on" action for SimpleHTTPPlugin"""

    data = '<BinaryState>1</BinaryState>'

    resp = requests.post('http://127.0.0.1:12345/upnp/control/basicevent1',
                         data=data)
    assert resp.status_code == 200


def test_old_config_fails() -> None:
    """Ensure the config for fauxmo < v0.4.0 fails with SystemExit"""

    with pytest.raises(SystemExit):
        fauxmo.main(config_path_str="tests/old-config-sample.json")


def test_simplehttpplugin(simplehttpplugin_target: pytest.fixture) -> None:
    """Tests simplehttpplugin

    Uses the fauxmo_device fixture (runs httpbin) to emulate the *target* of
    SimpleHTTPPlugin's `on_cmd` and `off_cmd`, ensures these run and return
    200, which should make the `.on()` and `.off()` methods return True.
    """

    with open("tests/test_config.json") as f:
        config = json.load(f)

    for device in config["PLUGINS"]["SimpleHTTPPlugin"]["DEVICES"]:
        assert SimpleHTTPPlugin(**device).on() is True
        assert SimpleHTTPPlugin(**device).off() is True
