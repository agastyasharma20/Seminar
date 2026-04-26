from .utils import get_event_settings


def event_settings(request):
    return {"event_settings": get_event_settings()}
