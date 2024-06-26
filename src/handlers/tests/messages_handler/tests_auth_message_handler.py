import pytest
from datetime import UTC, datetime

from app.types import DecodedValidToken
from handlers.dto import SuccessResponseMessage
from handlers.exceptions import WebsocketMessageException
from handlers.messages_handler import WebSocketMessagesHandler
from storage.storage_updaters import StorageWebSocketRegister

pytestmark = [
    pytest.mark.usefixtures("set_jwt_public_key"),
]


@pytest.fixture
def ya_user_decoded_valid_token():
    return DecodedValidToken(sub="ya_user", exp="4852128170")


@pytest.fixture
def auth_handler(message_handler: WebSocketMessagesHandler, ws):
    return lambda auth_message: message_handler.handle_auth_message(ws, auth_message)


def test_auth_handler_response_on_correct_auth_message(auth_handler, auth_message):
    auth_response = auth_handler(auth_message)

    assert isinstance(auth_response, SuccessResponseMessage)
    assert auth_response.message_type == "SuccessResponse"
    assert auth_response.incoming_message == auth_message


def test_auth_handler_register_websocket_in_storage(auth_handler, ws, auth_message, mocker, storage):
    spy_websocket_register = mocker.spy(StorageWebSocketRegister, "__call__")

    auth_handler(auth_message)

    assert storage.is_websocket_registered(ws) is True
    spy_websocket_register.assert_called_once()
    called_service = spy_websocket_register.call_args.args[0]
    assert called_service.storage == storage
    assert called_service.websocket == ws
    assert called_service.validated_token == DecodedValidToken(sub="user", exp=4700000000)


def test_auth_handler_raise_if_user_send_token_for_different_user(auth_handler, auth_message, storage, ws, register_ws, ya_user_decoded_valid_token):
    register_ws(ws, ya_user_decoded_valid_token)

    with pytest.raises(WebsocketMessageException) as exc_info:
        auth_handler(auth_message)  # send valid user1 token while connection registered with ya_user

    raised_exception = exc_info.value
    assert raised_exception.errors == ["The user has different public id"]
    assert raised_exception.incoming_message == auth_message
    assert storage.is_websocket_registered(ws) is True, "The existed connection should not be touched"


@pytest.mark.freeze_time(datetime.fromtimestamp(4700000001, tz=UTC))  # one second after token expiration
def test_auth_handler_raise_if_user_try_to_auth_with_expired_token(auth_handler, ws, auth_message, storage):
    with pytest.raises(WebsocketMessageException) as exc_info:
        auth_handler(auth_message)

    raised_exception = exc_info.value
    assert raised_exception.errors == ["Signature has expired"]
    assert raised_exception.incoming_message == auth_message
    assert storage.is_websocket_registered(ws) is False, "The ws should not be added to registered websockets"
