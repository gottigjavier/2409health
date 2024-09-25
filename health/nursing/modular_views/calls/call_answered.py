from django.http import JsonResponse
from ...models import Call, Bed
from ..app.app_load import load
from ..app.app_ws_update import ws_load
import json


# ----------------------------------------------------------------------------------------
# for dev test usin rooms.js need recive parameter (bed) from consumer.py
# --> ans_call = await sync_to_async(answ_call)(bed)

# for prod using only mosquitto just use "ws_load" in consumer.py
# --> from .modular_views.app.app_ws_update import ws_load
# --> ans_call = await sync_to_async(ws_load)
# Managed by try and except in consumer.py

def answ_call(bed):
    return ws_load()

# -----------------------------------------------------------------------------------------

def call_answered(request):
    data = json.loads(request.body)
    calls_list = data['saveCallsList']
    for answ_call in calls_list:
        call = Call.objects.get(bed__id_bed=answ_call['bed'], state='active')
        if call:
            try:
                bed = Bed.objects.get(id_bed=answ_call['bed'], active=True)
                call.response_time = answ_call['response_time'].replace("T", " ")
                call.state = 'answered'
                if bed.bed_state == 'call-task':
                    bed.bed_state = 'task'
                else:
                    bed.bed_state = 'occupied'
                bed.save()
                call.save()
            except:
                return JsonResponse({"message": "Bed answered Error."}, status=400)
        else:
            return JsonResponse({"message": "Call does not exist."}, status=400)
    return load()