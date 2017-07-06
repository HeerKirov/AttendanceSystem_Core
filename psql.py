import psycopg2
from config import database as db_config
from datetime import datetime, timedelta, date


def connect(**kwargs):
    return connect_by(kwargs['host'], kwargs['port'], kwargs['database'], kwargs['username'], kwargs['password'])

# 这些数据是实时获得的，需要手动修改
now_year = 2017
now_term = 3
now_weeks = 1
now_weekday = 3
now_course_number = 1
course_begin_time = '2017-07-06 10:10:00'
course_end_time = '2017-07-06 11:00:00'


def connect_by(host, port, database, username, password):
    print("Connect to database to modify attendance data. YEAR = %s, TERM = %s, WEEK = %s, WEEKDAY = %s, COURSE = %s"
          % (now_year, now_term, now_weeks, now_weekday, now_course_number))
    conn = psycopg2.connect(host=host, port=port, database=database, user=username, password=password)
    cur = conn.cursor()
    cur.execute("SELECT id_id, username from main_asstudent;")  # 查询所有的AsStudent的id。
    for student_id, user_id in cur.fetchall():
        # 获得学生modelID(用于DB) 学号(id)
        print("Student ID: %s" % (user_id,))
        # 根据MtoM关系表查所有与该学生关联的课程的ID。
        cur.execute("SELECT course_id from main_asstudent_course_set where asstudent_id = %s;" % (student_id,))
        courses = []  # 准备将valid的课程ID加入这个列表
        for course_id, in cur.fetchall():
            # course_id = course_relation[0]  # 获得Course的编号(id)
            # 查某一门具体课程的year term
            cur.execute("SELECT id, year, term from main_course where id = '%s' limit 1;" % (course_id,))
            _, course_year, course_term = cur.fetchone()
            # 筛掉那些不是当前学期的课程
            if course_year == now_year and course_term == now_term:
                courses.append(course_id)
        now_course_record = None  # 记录应在的(课程, 教室) None表示无课 否则表示有课
        for course_id in courses:
            if now_course_record is not None:
                break
            # 对于某一门课，查询其所有的上课时间数据。
            cur.execute("SELECT classroom_id, weeks, weekday, course_number from main_courseschedule "
                        "where course_id = '%s';" % (course_id,))
            for classroom_id, weeks_str, weekday_str, course_number_str in cur.fetchall():
                weeks = iter(int(i) for i in weeks_str.split(','))
                weekday = iter(int(i) for i in weekday_str.split(','))
                course_number = iter(int(i) for i in course_number_str.split(','))
                if now_weeks in weeks and now_weekday in weekday and now_course_number in course_number:
                    # 该判断条件确认此课程是上一节课。
                    now_course_record = (course_id, classroom_id)
                    break
        if now_course_record is not None:  # 确实有课，应当进行出勤记录写入
            # 取所有与该节次时间有关联的ClassroomRecord，并取第一个
            course_id, classroom_id = now_course_record
            print("Found course. Course = %s, Classroom = %s." % now_course_record)
            # 接下来筛出首条有关联的教室使用记录。
            sql = "select time_in, time_out from main_classroomrecord " \
                  "where student_id = %s and classroom_manage_id = '%s' " \
                  "and time_in <= '%s' and (time_out ISNULL or time_out >= '%s') " \
                  " LIMIT 1;" % (student_id, classroom_id, course_end_time, course_begin_time)
            cur.execute(sql)
            record = cur.fetchone()
            format_string = '%Y-%m-%d %H:%M:%S'
            today_date = datetime.strptime(course_begin_time, format_string)
            if record is not None:  # 查到了相关记录
                interval = timedelta(minutes=15)
                time_in, time_out = record[0].replace(tzinfo=None), record[1].replace(tzinfo=None)   # 这是实际时间
                time_begin, time_end = datetime.strptime(course_begin_time, format_string), \
                                       datetime.strptime(course_end_time, format_string)  # 课程安排时间
                time_late, time_leave = time_begin + interval, time_end - interval  # 迟早早退临界时间
                print("Course[%s to %s], Record[%s to %s]" % (time_begin, time_end, time_in, time_out))
                if time_in <= time_begin and time_out >= time_end:  # 完全占据了课堂时间，正常状态
                    status = 'NORMAL'
                elif time_in > time_late or time_out < time_leave:  # 只要一个点超出临界点就视作缺勤
                    status = 'ABSENT'
                elif time_begin <= time_in <= time_late:  # 迟到
                    status = 'LATE'
                elif time_leave <= time_out <= time_end:  # 早退
                    status = 'LEAVE'
                else:  # 虽然应该没有这么个情况，但还是加一个未到。
                    status = 'NONE'
            else:  # 没有查到相关记录，这是缺勤
                status = 'ABSENT'
                time_in = datetime.strptime(course_end_time, format_string)
            print("STATUS = %s" % (status,))
            # 这里需要做一个防重复检测。
            # 首先查询attendance中是否存在date&course_number&student_id&course_manage_id一致的记录，如果存在，就选择更新该记录。
            # 如果不存在，就选择创建新记录。
            sql = "select count(id) from main_attendancerecord " \
                "where course_number = %s and date = '%s' and student_id = %s and course_manage_id = '%s';" \
                % (now_course_number, today_date, student_id, course_id)
            print(sql)
            cur.execute()
            print(cur.fetchall())
            cur.execute()
            sql = "insert into main_attendancerecord (course_number, status, student_id, course_manage_id, date) " \
                  "values(%s, '%s', %s, '%s', '%s');" % (now_course_number, status, student_id, course_id, today_date)
            cur.execute(sql)

        else:
            print("Not found course.")
    # conn.commit()
    conn.close()

if __name__ == '__main__':
    connect(**db_config)
