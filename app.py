from apscheduler.schedulers.blocking import *
from apscheduler.schedulers.background import *
import schedule
from datetime import datetime
import config


def get_attendance_task(begin, end, number):
    begin_time, end_time, no = begin, end, number

    def task_def():
        print("Task Triggered [%s to %s of No.%s]" % (begin_time, end_time, no))
    return task_def


def get_datetime(time_str):
    h, m, s = time_str.split(':')
    date = datetime.now()
    return datetime(date.year, date.month, date.day, int(h), int(m), int(s))


task = BackgroundScheduler()


def make_every_day(task_scheduler):
    """
    每天0点执行的计划任务。
    销毁上一天的所有任务安排并从API读取下一天的任务安排,然后创建新的任务。
    :return: None
    """

    print("Make schedule data every day in %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    sches = schedule.get_schedule(config.api['server'] + config.api['schedule'])
    if sches is not None:
        sched = task_scheduler
        for item in sches:  # 按照计划，对每一个下课时间生成一个计划任务。
            sched.add_job(get_attendance_task(item['begin'], item['end'], item['no']), 'date',
                          run_date=get_datetime(item['end']), misfire_grace_time=60)
            print("Add new schedule task in %s" % (item['end'],))
    else:
        print("Exception happened while getting schedule data.Please check config or server.")


if __name__ == '__main__':
    task.start()
    make_every_day(task)  # 在启动corn时也执行一次初始化
    scheduler = BlockingScheduler()
    scheduler.add_job(make_every_day, 'cron', hour='0')
    print("Schedule Running.")
    scheduler.start()
    print("End.")
