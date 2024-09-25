import pandas as pd
from datetime import datetime
from ..models import Record

# ------------------ Record ---------------------------------
def recording(loged_user, action, before, after):
    record = Record()
    try:
        record.loged_user = loged_user
        record.action = action
        record.time = datetime.now()
        record.before = before
        record.after = after
        record.save()
        return
    except:
        print ('Error. Record no saved')
        return
# ---------------- End of Record ----------------------------


# ---------------- Begin Data Analytics ----------------------------

def data_analytics():
    datas = Record.objects.all()
    if datas:
        serialized_data = [data.serialize() for data in datas]
    else:
        serialized_data = []
    #print(serialized_data)
    df = pd.DataFrame(serialized_data)
    recording_path = "nursing/record/recording.csv"
    df.to_csv(recording_path, sep=";")
    print("Data for Analysis saved in: " + recording_path)

# ---------------- end Data Analytics ----------------------------