import pytest

from app.types import DecodedValidToken
from storage import SubscriptionStorage
from storage.storage_updaters.storage_user_subscriber import StorageUserSubscriber
from storage.storage_updaters.storage_websocket_register import StorageWebSocketRegister


@pytest.fixture
def storage():
    return SubscriptionStorage()


@pytest.fixture
def valid_token():
    return DecodedValidToken(sub="user1", exp=4700000000)  # year of expiration 2118


@pytest.fixture
def ya_valid_token():
    return DecodedValidToken(sub="user1", exp=5700000000)


@pytest.fixture
def ya_user_valid_token():
    return DecodedValidToken(sub="user2", exp=7700000000)


@pytest.fixture
def register_ws(storage):
    def register(ws, token):
        StorageWebSocketRegister(storage, ws, token)()

    return register


@pytest.fixture
def ws_registered(ws, valid_token, register_ws):
    register_ws(ws, valid_token)
    return ws


@pytest.fixture
def event():
    return "boobs"


@pytest.fixture
def ya_event():
    return "boobs-boobs"


@pytest.fixture
def subscribe_ws(storage):
    def subscribe(ws, event):
        StorageUserSubscriber(
            storage=storage,
            websocket=ws,
            event=event,
        )()

    return subscribe


@pytest.fixture
def ws_subscribed(ws_registered, subscribe_ws, event):
    subscribe_ws(ws_registered, event)
    return ws_registered


@pytest.fixture
def ws_register_and_subscribe(register_ws, subscribe_ws):
    def register_and_subscribe(ws, token, event):
        register_ws(ws, token)
        subscribe_ws(ws, event)
        return ws

    return register_and_subscribe
