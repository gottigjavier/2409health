from datetime import datetime
from ...models import Task, Bed
from apscheduler.schedulers.background import BackgroundScheduler
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from ..beds.beds_serialized import serial_beds
from django.db.models import Min
from ..app.app_ws_update import app_ws_update


scheduler = BackgroundScheduler()
scheduler.start()


def tasks_ws_update():
    tasks = Task.objects.filter(active=True).order_by("programed_time").all()
    if tasks:
        time_now = datetime.now()
        time_now_float = time_now.timestamp()
        for task in tasks:
            task_time = task.programed_time.timestamp()
            bed = Bed.objects.get(pk=task.bed.pk)
            # compute 10-minute window before programed_time -> 'soon'
            if task_time - time_now_float > 0:
                if task_time - time_now_float <= 600:
                    task.state = "soon"
                else:
                    task.state = "later"
            else:
                task.state = "passed"
                if bed.bed_state == "call":
                    bed.bed_state = "call-task"
                if bed.bed_state == "occupied":
                    bed.bed_state = "task"
            bed.save()
            task.save()
        tasks = Task.objects.filter(active=True).order_by("programed_time").all()
        beds = Bed.objects.filter(active=True).all()
        beds_list = serial_beds(beds)
        tasks_list = [task.serialize() for task in tasks]
        tasks_and_beds = {"beds_list": beds_list, "tasks_list": tasks_list}
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            "tasksboard",
            {
                "type": "deprocessing",
                "tasks_and_beds": tasks_and_beds,
            },
        )
        # Also update the full app state so appboard subscribers get the change
        try:
            app_ws_update()
        except Exception as e:
            print(f"Error broadcasting app_ws_update from tasks_ws_update: {e}")
        tasks_scheduler()


def first_programed():
    soon_task_programed = (
        Task.objects.filter(active=True)
        .filter(state="soon")
        .aggregate(sched_time=Min("programed_time"))
    )
    later_task_programed = (
        Task.objects.filter(active=True)
        .filter(state="later")
        .aggregate(sched_time=Min("programed_time"))
    )
    if soon_task_programed["sched_time"]:
        soon_task_programed_float = soon_task_programed["sched_time"].timestamp()
        soon_task_programed = soon_task_programed["sched_time"]
    else:
        soon_task_programed_float = 10000000000.0  # Date: 2286-11-20 14:46:40
        soon_task_programed = datetime.fromtimestamp(soon_task_programed_float)
    if later_task_programed["sched_time"]:
        later_task_programed_minus_10_float = (
            later_task_programed["sched_time"].timestamp() - 600
        )
        later_task_programed = datetime.fromtimestamp(
            later_task_programed_minus_10_float
        )
    else:
        later_task_programed_minus_10_float = 10000000100.0
        later_task_programed = datetime.fromtimestamp(
            later_task_programed_minus_10_float
        )
    if soon_task_programed_float < later_task_programed_minus_10_float:
        return soon_task_programed
    else:
        return later_task_programed


def tasks_scheduler():
    first_task_programed = first_programed()
    print("next query to db ", first_task_programed)
    scheduler.add_job(
        tasks_ws_update,
        "date",
        run_date=first_task_programed,
        id="task_sched",
        replace_existing=True,
    )
