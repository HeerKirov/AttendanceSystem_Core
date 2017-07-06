import requests
import psql
from datetime import datetime


def get_schedule(url):
    r = requests.get(url)
    try:
        e = r.json()
        return e['year'], e['term'], e['begin'], e['end'], e['items']
    except Exception:
        return None


def get_attendance_task(database, check):
    def task_def():
        """
        触发下课时间的定时任务。仅执行一次就销毁。
        :return: 
        """
        print("Task Triggered [%s to %s of No.%s]" % (check['begin_time'], check['end_time'], check['course_number']))
        psql.connect(database, check)
    return task_def


def calc_weeks(begin_time, goal_time):
    """
    计算goal_time在以begin_time为第一周的情况下是周几，以及是星期几。
    :param begin_time: 开始时间
    :param goal_time: 目标时间
    :return: (weeks, weekday)
    """
    begin_weekday, goal_weekday = begin_time.weekday(), goal_time.weekday()  # 这个是以0为基数的weekday。
    delta = goal_time - begin_time
    return (delta.days + begin_weekday) // 7 + 1, goal_weekday + 1

