"""Authenticated per-device notification controls. Subscription secrets never leave status."""

from fastapi import Depends, Response

from .auth import rate_limit
from .errors import DomainError
from .reminders import PushQueued, PushRegistration, PushRetried, PushSettings, PushStatus, PushTest


def register_routes(app, session, service):
    prefix = "/api/v1/notifications/push"

    def budget(current, action, maximum=20):
        with service.database.transaction() as db:
            allowed = rate_limit(db, "push." + action + ":" + current["device_id"], maximum, 3600)
        if not allowed:
            raise DomainError("push_request_limit", 429)

    @app.get(prefix, response_model=PushStatus)
    def status(current=Depends(session)):
        return service.status(current["device_id"])

    @app.put(prefix + "/subscription", response_model=PushStatus)
    def subscribe(body: PushRegistration, current=Depends(session)):
        budget(current, "subscribe")
        return service.register(current, body)

    @app.put(prefix + "/preferences", response_model=PushStatus)
    def preferences(body: PushSettings, current=Depends(session)):
        budget(current, "preferences", 120)
        return service.set_preferences(current, body)

    @app.delete(prefix + "/subscription", status_code=204)
    def unsubscribe(current=Depends(session)):
        service.remove(current["device_id"])
        return Response(status_code=204)

    @app.post(prefix + "/test", status_code=202, response_model=PushQueued)
    def test(body: PushTest, current=Depends(session)):
        budget(current, "test", 10)
        service.queue_test(current["device_id"], str(body.request_id))
        return PushQueued()

    @app.post(prefix + "/retry", status_code=202, response_model=PushRetried)
    def retry(current=Depends(session)):
        budget(current, "retry", 10)
        return PushRetried(count=service.retry(current["device_id"]))
