import json
from datetime import datetime
from ...models import Call, Bed
from ..app.app_ws_update import ws_load 


def new_call(bed):
    try:
        active_bed = Bed.objects.get(id_bed=bed, active=True)
    except:
        active_bed = {}
    try:
        call = Call.objects.get(state='active', bed__id_bed=bed)
    except:
        call = {}
    if not active_bed == {} and call == {}:
        if active_bed.bed_state == 'task':
            active_bed.bed_state = 'call-task'
        else:
            active_bed.bed_state = 'call'
        active_bed.save()
        new_call = Call()
        new_call.bed = active_bed
        new_call.call_time = datetime.now()
        new_call.response_time = datetime.now()
        new_call.state = 'active'
        new_call.save()
        return ws_load()
    else:
        pass
