# -*- coding: UTF-8 -*-
import datetime

from app.api.errors import bad_request
from . import bp
from pprint import pprint
from flask import request, jsonify
from app.models import db
from app.libs.add_task import add_task
from app.models.task import Task
from app.extensions import scheduler
from app.task.test_task import my_job


@bp.route('/test_db', methods=['GET'])
def test_db(task_id=1):
    data = db.session.execute(f"select next_run_time from apscheduler_jobs where id = {task_id}")
    data = [dict(zip(d.keys(), d)) for d in data]
    print(data)
    return jsonify(
        {
            'data': data,
            'msg': '定时任务开始成功',
            'status': '200'
        }
    )


@bp.route('/start_aps', methods=['GET'])
def start_aps():
    try:
        # scheduler.init_app(app)
        scheduler.start()
        return jsonify(
            {
                'msg': '定时任务开始成功',
                'status': '200'
            }
        )
    except Exception as e:
        raise e
        # return jsonify(
        #     {
        #         'error': str(e)
        #     }
        # )


@bp.route('/task/list', methods=['GET'])
def task_list():
    """ 任务列表 """
    filterlist = []
    id = request.args.get('id')
    page = int(request.args.get('page'))
    per_page = int(request.args.get('limit'))
    project = request.args.get('project', '')
    env = request.args.get('env', '')
    filterlist.append(Task.is_valid==True)
    if project:
        filterlist.append(Task.project.like('%' + project + '%'))
    if env:
        filterlist.append(Task.env == env)
    if id:
        filterlist.append(Task.id == id)
    data = Task.query.filter(*filterlist)
    if project is None and env is None:
        data = Task.query.filter_by(is_valid=True)
    data = Task.to_collection_dict(data, page, per_page, 'web.task_list')
    return jsonify(data)

    # filterlist = []

    # jobs = scheduler.get_jobs()
    # l = []
    # d = []
    # data = str(jobs)
    # list = data.split(',')
    # for i in list:
    #     r = re.findall(r'\((id=.+ name=.+)\)', i)
    #     r = r[0].split(' ')
    #     for i in r:
    #         r = i.split('=')
    #         l.append(r)
    #     dd = dict(l)
    #     d.append(dd)
    # return d

    # page = int(request.args.get('page'))
    # per_page = int(request.args.get('limit'))
    # task_name = request.args.get('task_name', '')
    # env = request.args.get('env', '')
    #
    # filterlist.append(Task.is_valid==True)
    #
    # if task_name:
    #     filterlist.append(Task.task_name.like('%' + task_name + '%'))
    # if env:
    #     filterlist.append(Task.env == env)
    #
    # data = Task.query.filter(*filterlist)
    #
    # if task_name is None and env is None:
    #     data = Task.query.filter_by(is_valid=True)
    # data = Task.to_collection_dict(data, page, per_page, 'web.task_list')
    # return jsonify(data)


# 新增job
@bp.route('/addCron', methods=['post'])
def add_cron():
    job = {}
    response = {'status': False}
    jobargs = request.get_json()
    id = jobargs['task_id']
    name = jobargs['task_name']
    trigger_type = jobargs['trigger_type']
    if trigger_type == "date":
        run_time = jobargs['run_time']

        try:
            scheduler.add_job(
                jobstore='default',
                func='app.task.test_task:my_job',
                trigger=trigger_type,
                run_date=run_time,
                replace_existing=True,
                coalesce=True,
                id=id,
                name=name,
            max_instances=1)
            response['status'] = True
            response['msg'] = "job[%s] addjob success!" % id
            add_task(jobargs)
            print("添加一次性任务成功---[ %s ] " % id)

        except Exception as e:
            response['msg'] = str(e)

    elif trigger_type == 'interval':
        seconds = jobargs['interval_time']
        seconds = int(seconds)
        if seconds <= 0:
            raise TypeError('请输入大于0的时间间隔！')
        try:
            scheduler.add_job(
                jobstore='default',
                func='app.task.test_task:my_job',
                              trigger=trigger_type,
                              seconds=seconds,
                              replace_existing=True,
                              coalesce=True,
                              id=id,
                              name=name,
            max_instances=1)
            response['status'] = True
            add_task(jobargs)
            print("添加周期执行任务成功任务成功---[ %s ] " % id)
        except Exception as e:
            response['msg'] = str(e)

    elif trigger_type == "cron":
        day_of_week = jobargs["run_time"]["day_of_week"]
        hour = jobargs["run_time"]["hour"]
        minute = jobargs["run_time"]["minute"]
        second = jobargs["run_time"]["second"]
        try:
            scheduler.add_job(
                jobstore='default',
                func='app.task.test_task:my_job',
                              id=id,
                              name=name,
                              trigger=trigger_type,
                              day_of_week=day_of_week,
                              hour=hour,
                              minute=minute,
                              second=second,
                              replace_existing=True,
            max_instances=1)
            response['status'] = True
            add_task(jobargs)
            print("添加周期执行任务成功任务成功---[ %s ]" % id)
        except Exception as e:
            response['msg'] = str(e)
    return jsonify({
            "status": 200,
            "data": "success",
            'response': response
        })


# 暂停
@bp.route('/pause/task', methods=['GET'])
def pause_job():
    task_id = request.args.get('task_id')
    response = {'status': False}
    try:
        scheduler.pause_job(task_id)
        response['status'] = True
        response['msg'] = "job[%s] pause success!" % task_id
        task = Task.query.filter(Task.task_id == task_id).first()
        task.status = 0
        db.session.commit()
    except Exception as e:
        response['msg'] = str(e)
    pprint(response)
    return ({
        "status": 200,
        "data": "success",
        "task_status": 0,
        "next_run_time": None,
        "response": response
    })


#启动
@bp.route('/resume/task', methods=['GET'])
def resume_job():
    task_id = request.args.get('task_id')
    response = {'status': False}
    try:
        scheduler.resume_job(task_id)
        response['status'] = True
        response['msg'] = "job[%s] resume success!" % task_id
        task = Task.query.filter(Task.task_id == task_id).first()
        task.status = 1
        db.session.commit()
        next_run_time = db.session.execute(f"select next_run_time from apscheduler_jobs where id = {task_id}")
        next_run_time = [dict(zip(d.keys(), d)) for d in next_run_time][0]['next_run_time']
        if next_run_time:
            time = datetime.datetime.fromtimestamp(next_run_time)
            time = time.strftime("%Y-%m-%d %H:%M:%S")
            return ({
                "status": 200,
                "data": "success",
                "task_status": 1,
                "next_run_time": time,
                "response": response
            })
    except Exception as e:
        response['msg'] = str(e)
    return (bad_request(response['msg']))


@bp.route('/info/task', methods=['GET'])
def get_jobinfo():
    # task_id = request.args.get('task_id')
    response = {'status': False}
    try:
        # print(type(task_id))
        # ret_list = scheduler.get_job(task_id)
        jobs = scheduler.get_jobs()
        # jobss = scheduler.print_jobs()
        response['jobs'] = str(jobs)
        # print(jobss)
        # print(ret_list)
    except Exception as e:
        response['msg'] = str(e)
    return jsonify(
        {
        "status": 200,
        "data": "success",
        'response': response
    })
