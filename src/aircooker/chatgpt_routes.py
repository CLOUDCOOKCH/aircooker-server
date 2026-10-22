"""Personal-session controls and a one-use, short-lived helper pairing capability."""

from importlib.resources import files

from fastapi import Depends, Response

from .chatgpt_models import (
    ChatGPTBootstrap,
    ChatGPTClaim,
    ChatGPTComplete,
    ChatGPTDisconnect,
    ChatGPTModelCatalog,
    ChatGPTPairing,
    ChatGPTPairRequest,
    ChatGPTSelection,
    ChatGPTStatus,
)


def register_routes(app, session, service):
    prefix = "/api/v1/integrations/chatgpt"

    @app.get(prefix, response_model=ChatGPTStatus)
    def status(current=Depends(session)):
        return service.status(current["id"])

    @app.post(prefix + "/pairing", status_code=201, response_model=ChatGPTPairing)
    def prepare(body: ChatGPTPairRequest, current=Depends(session)):
        return service.prepare(current["id"])

    @app.delete(prefix + "/pairing", status_code=204)
    def cancel(current=Depends(session)):
        service.cancel_pairing(current["id"])
        return Response(status_code=204)

    # The helper has no household password/session. These two endpoints accept only
    # the unguessable capability explicitly supplied by the authenticated owner.
    @app.post(prefix + "/pairing/claim", response_model=ChatGPTBootstrap)
    def claim(body: ChatGPTClaim):
        return service.claim(body.code.get_secret_value())

    @app.post(prefix + "/pairing/complete", response_model=ChatGPTStatus)
    def complete(body: ChatGPTComplete):
        return service.complete(body)

    @app.get(prefix + "/models", response_model=ChatGPTModelCatalog)
    def models(current=Depends(session)):
        return service.models(current["id"])

    @app.put(prefix, response_model=ChatGPTStatus)
    def select(body: ChatGPTSelection, current=Depends(session)):
        return service.select(current["id"], body)

    @app.delete(prefix, response_model=ChatGPTDisconnect)
    def disconnect(current=Depends(session)):
        return service.disconnect(current["id"])

    @app.get(prefix + "/helper", response_class=Response)
    def helper():
        return Response(
            files("aircooker").joinpath("chatgpt_helper.py").read_bytes(),
            media_type="text/x-python",
            headers={"Content-Disposition": 'attachment; filename="mealf-connect-chatgpt.py"'},
        )
