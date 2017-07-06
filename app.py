from apscheduler.schedulers.blocking import *
from apscheduler.schedulers.background import *
import schedule
from datetime import datetime, date
import config


def get_datetime(time_str):
    h, m, s = time_str.split(':')
    date = datetime.now()
    return datetime(date.year, date.month, date.day, int(h), int(m), int(s))


task = BackgroundScheduler()


def make_every_day():
    """
    每天0点执行的计划任务。
    销毁上一天的所有任务安排并从API读取下一天的任务安排,然后创建新的任务。
    :return: None
    """
    print("Make schedule data every day in %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    sches = schedule.get_schedule(config.api['server'] + config.api['schedule'])
    if sches is not None:
        sche_year, sche_term, sche_begin, sche_end, sche_items = sches
        sched = task
        sche_weeks, sche_weekday = \
            schedule.calc_weeks(datetime.date(datetime.strptime(sche_begin, '%Y-%m-%d')), datetime.date(datetime.now()))
        for item in sche_items:  # 按照计划，对每一个下课时间生成一个计划任务。
            check = {
                'year': sche_year,
                'term': sche_term,
                'weeks': sche_weeks,
                'weekday': sche_weekday,
                'course_number': item['no'],
                'begin_time': item['begin'],
                'end_time': item['end']
            }
            sched.add_job(schedule.get_attendance_task(config.database, check), 'date',
                          run_date=get_datetime(item['end']), misfire_grace_time=60)
            print("Add new schedule task in %s" % (item['end'],))
    else:
        print("Exception happened while getting schedule data.Please check config or server.")


if __name__ == '__main__':
    task.start()
    make_every_day()  # 在启动corn时也执行一次初始化
    scheduler = BlockingScheduler()
    scheduler.add_job(make_every_day, 'cron', hour='0')
    print("Schedule Running.")
    scheduler.start()
    print("End.")
