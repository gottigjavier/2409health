# import pandas as pd
from datetime import datetime
from ..models import Event


# ------------------ Event ---------------------------------
def save_event(loged_user, action, before, after):
    event = Event()
    try:
        event.loged_user = loged_user
        event.action = action
        event.time = datetime.now()
        event.before = before
        event.after = after
        event.save()
        return
    except Exception as e:
        print("Error. Event no saved ", e)
        return


# ---------------- End of Event ----------------------------


# ---------------- Begin Data Analytics ----------------------------


# Unused
def data_analytics():
    pass
    #datas = Event.objects.all()
    #if datas:
    #    serialized_data = [data.serialize() for data in datas]
    #else:
    #    serialized_data = []
    #df = pd.DataFrame(serialized_data)
    #events_path = "nursing/event/events.csv"
    #df.to_csv(events_path, sep=";")
    #print("Data for Analysis saved in: " + events_path)


# ---------------- end Data Analytics ----------------------------
