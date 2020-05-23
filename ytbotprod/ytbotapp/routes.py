from flask import render_template, flash, redirect, url_for, request, Markup
import json
from ytbotapp import app
from ytbotapp.forms import NewList,NewComm,NewScannerForm,AccountForm,TaskForm
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
#from google.oauth2.credentials import Credentials
from ytbotapp.classes import CommTask, Scanner, getchannelname
import os
import multiprocessing
import asyncio
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
# from flask_apscheduler import APScheduler
# from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from uuid import uuid1
from datetime import date, datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


CLIENT_SECRETS_FILE='clientsecret.json'
auth=HTTPBasicAuth()
users={"admin":generate_password_hash("bananasplit")}
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

def schedulejobs():
    with open('commenttasks.json')  as tasks:
        taskdict=json.load(tasks)
        for task in taskdict:
            if taskdict[task][5]=='daily':
                botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
                apsched.add_job(func=botexec.execute, trigger='interval', days=1, executor='processpool', id=str(task)+'scheduler'+str(taskdict[task][2]))
            elif taskdict[task][5]=='every 3 days':
                botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
                apsched.add_job(func=botexec.execute, trigger='interval', days=3, executor='processpool', id=str(task)+'scheduler'+str(taskdict[task][2]))
            elif taskdict[task][5]=='once every week':
                botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
                apsched.add_job(func=botexec.execute, trigger='interval', days=7, executor='processpool', id=str(task)+'scheduler'+str(taskdict[task][2]))

def commstoruntoday():
    comms=0
    for job in apsched.get_jobs():
            daystojob=(date.today()-datetime.strptime(str(job.next_run_time)[:10], '%Y-%m-%d').date()).days
            print(job.id)
            if daystojob<1:
                if job.id[45:]:
                    comms=comms+int(job.id[45:])
    return comms

def commspostedtoday():
    comms=0
    with open('commentdata.json') as data:
        commhistory=json.load(data)
        for comm in commhistory:
            commdate=datetime.strptime(commhistory[comm][4][:10], '%Y-%m-%d').date()
            dayssincecomm=(date.today()-commdate).days
            if dayssincecomm<1:
                comms=comms+1
    return comms

def scanchannels():
    try:
        with open('scanners.json') as scanrs:
            scanners=json.load(scanrs)
    except:
        scanners={}
    for scanner in scanners:
        activ=Scanner(scanner, scanners[scanner][0], scanners[scanner][1])
        asyncio.run(activ.scan())


def threaded():
   executor = ThreadPoolExecutor(5)
   future = executor.submit(scanchannels())


def allendswith(end):
    result=[]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    for root, dirs, files in os.walk(os.path.join(dir_path,"..")): 
        for file in files: 
            if file.endswith(end): 
                result.append(str(file)[:-9])
    return result

executors = {
    'processpool': ProcessPoolExecutor(40)
}
apsched = BackgroundScheduler(executors=executors, job_defaults={'misfire_grace_time': 180})
# apsched.init_app(app)
apsched.start()
#threaded()
# apsched.add_job(func=threaded, trigger='interval', minutes=1, id='scannerscheduler', max_instances=5, executor='processpool')
@app.before_request
def flasherrors():
    with open('errors.json') as er:
        errors=json.load(er)
    for error in errors:
        flash(Markup(error), 'danger')
    with open('errors.json', 'w') as erw:
        json.dump({},erw)    
@app.context_processor
def sub_list():
    
    try:
        with open('comms.json') as data:
            commdict=json.load(data)
        return {"data": commdict}
    except:
        commdict={}
        return {"data": commdict}

@app.route('/logout')
def Logout():
        return "<h3>Logged out.</h1><br><a href='/index'>Log In<a>", 401   
    
@app.route('/')
@app.route('/index')
@auth.login_required
#@register_breadcrumb(app, '.', 'Home')
def index():
        return render_template('index.html', title='Dashboard')

        
@app.route('/statistics')
@auth.login_required
def statistics():
    flash('Keep your comments under 150 per day','warning')
    try:
        with open('scanners.json') as scans:
            scns=json.load(scans)
            scansno=len(scns)
            with open('commentdata.json') as data:
                datadict=json.load(data)
                f_date = date(2020, 5, 5)
                l_date = date.today()
                delta = l_date - f_date
                commnum=len(datadict)
                scans=0
                for comm in datadict:
                        if datadict[comm][5]=='scanner comment':
                            commdate=datetime.strptime(datadict[comm][4][:10], '%Y-%m-%d').date()
                            dayssincecomm=(date.today()-commdate).days
                            if dayssincecomm<1:
                                scans=scans+1
                avg=round(commnum/delta.days,2)
                return render_template('statistics.html', title='Statistics', commhistory=datadict,commnum=commnum, scans=scans, avg=avg, scansno=scansno, commsched=commstoruntoday(), commposted=commspostedtoday())
    except:
        return render_template('statistics.html', title='Statistics', commnum=0, scans=0, delta=1, scansno=0, commsched=0, commposted=0)
@app.route('/deletecommlog')
def delcommlog():
    with open('commentdata.json', 'w') as dta:
        json.dump({}, dta)
        flash('Data deleted', 'danger')
        return redirect('/statistics')

@app.route('/deletefromlog/<commkey>')
def delcommfromlog(commkey):
    with open('commentdata.json') as data:
        datadict=json.load(data)
    with open('commentdata.json', 'w') as w:
        datadict.pop(commkey)
        json.dump(datadict, w)
    flash('Data deleted', 'danger')
    return redirect('/statistics')

@app.route('/channelscanner/')
@app.route('/channelscanner')
@auth.login_required
def channelscanner():
    try:
        with open('scanners.json') as scanrs:
            scanners=json.load(scanrs)
    except:
        scanners={}
    return render_template('channelscanner.html', title='Channel Scanner', scanners=scanners)

@app.route('/channelscanner/newscanner', methods=['get', 'post'])
@auth.login_required
def newscanner():
    form=NewScannerForm()
    with open('comms.json') as comms:
        commentlists=json.load(comms)
    form.commentlist.choices=[(commentlist, commentlist) for commentlist in commentlists]
    accslist=allendswith('auth.json')
    form.account.choices=[(account, account) for account in accslist]
    if form.validate_on_submit():
        return redirect(f'/channelscanner/newscanner/{form.channelid.data}&{form.commentlist.data}&{form.account.data}')
    else: 
        print(form.errors)
    try:
        with open('scanners.json') as scanrs:
            scanners=json.load(scanrs)
    except:
        scanners={}
    return render_template('newscanner.html', title='New Scanner', form=form, scanners=scanners)

@app.route('/deletescanner/<scanner>')
@auth.login_required
def deletescanner(scanner):
    with open('scanners.json') as scanrs:
        scanners=json.load(scanrs)
        scanners.pop(scanner)
        with open('scanners.json','w+') as scanrs:
            json.dump(scanners, scanrs)
    flash(f'{scanner} deleted', 'danger')
    return redirect('/channelscanner')
    
@app.route('/channelscanner/newscanner/<channelid>&<commentlist>&<account>')
@auth.login_required
def startscanner(channelid, commentlist, account):
    try:
        channelname=getchannelname(channelid)
    except:
        channelname=channelid
    try:
        with open('scanners.json') as scanrs:
            scanners=json.load(scanrs)
            scanners.update({channelid:[commentlist, account, channelname]})
            with open('scanners.json','w+') as scanrs:
                json.dump(scanners, scanrs)
            flash(f'{channelname} added to scan queue', 'success')
            return redirect('/channelscanner')
    except:
        with open('scanners.json','w+') as scanrs:
            json.dump({channelid:[commentlist, account]}, scanrs)
        flash(f'{channelname} added to scan queue', 'success')
        return redirect('/channelscanner')

    
@app.route('/commentlists/')
@app.route('/commentlists')
@auth.login_required
def commentlists():
    indict={'1':['1','2','3']}
    try:
        with open('comms.json') as comms:
            return render_template('commentlists.html', commentlists=json.load(comms), title='Comment Lists')
    except:# json.decoder.JSONDecodeError or FileNotFoundError:
        with open('comms.json', 'w') as comms:
            json.dump(indict, comms)
        with open('comms.json') as comms:
            return render_template('commentlists.html', commentlists=json.load(comms), title='Comment Lists')

@app.route('/commentlists/newlist', methods=['GET','POST'])
@auth.login_required
def newlist():
    form=NewList()
    if form.validate_on_submit():
        with open('comms.json') as comms:
            commentlists=json.load(comms)
        commentlists[form.listname.data]=[]
        with open('comms.json', 'w') as comms:
            json.dump(commentlists, comms)
        flash(f'{form.listname.data} created', 'success')
        return redirect(f'/commentlists/editlist/{form.listname.data}')
    with open('comms.json') as comms:
        return render_template('newlist.html', title='New Comment List', commentlists=json.load(comms), form=form)

@app.route('/commentlists/editlist/<listname>')
@auth.login_required
def editlist(listname):
    with open('comms.json') as comms:
        commentlists=json.load(comms)
        return render_template('editlist.html', listname=listname, title='Edit List '+listname, commlist=commentlists[listname])

@app.route('/accounts')
@auth.login_required
def accounts():
    accs=allendswith('auth.json')
    return render_template('accounts.html', accountslist=accs)

@app.route('/accounts/newaccount', methods=['get','post'])
@auth.login_required
def newaccount():
    form=AccountForm()
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes="https://www.googleapis.com/auth/youtube.force-ssl", redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_url, _ = flow.authorization_url(prompt='consent')
    auth_url=format(auth_url)
    #flash(Markup(f'Your authorization code is <a href="{auth_url}">here. Open in new tab and paste code below</a>'),'is-info')
    if form.validate_on_submit():
        flow.fetch_token(code=form.code.data)
        creds=flow.credentials
        creds_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        with open(f'{form.accountname.data}auth.json', "w") as outfile:
            json.dump(creds_data, outfile)
        flash(f'{form.accountname.data} added', 'success')
        return redirect('/accounts')
       # return redirect(f'/accounts/newaccount/activate/{form.accountname.data}&{form.code.data}')
    else:
        print(form.errors)
    accs=allendswith('auth.json')
    return render_template('newaccount.html', form=form, accountslist=accs, auth_url=auth_url)

@app.route('/accounts/delete/<accountname>')
@auth.login_required
def deleteaccount(accountname):
    os.remove(f'{accountname}auth.json')
    flash(f'{accountname} account deleted', 'warning')
    return redirect('/accounts')
        
@app.route('/commentlists/editlist/<listname>/newcomm', methods=['GET', 'POST'])
@auth.login_required
def newomm(listname):
    comform=NewComm()
    if comform.validate_on_submit():
        with open('comms.json') as comms:
            commentlists=json.load(comms)
        commentlists[listname].append(comform.comment.data)
        with open('comms.json', 'w') as comms:
            json.dump(commentlists, comms)
        flash('Comment added', 'success')
        return redirect(f'/commentlists/editlist/{listname}/newcomm')
    else: print(comform.errors)
    with open('comms.json') as comms:
        commentlists=json.load(comms)    
    return render_template('newcomm.html', form=comform, listname=listname, commlist=commentlists[listname])
    
@app.route('/delete/list/<listname>')
@auth.login_required
def deletelist(listname):
    with open('comms.json') as comms:
        commentlists=json.load(comms)
    commentlists.pop(listname, None)
    with open('comms.json', 'w') as comms:
        json.dump(commentlists, comms)
    flash(f'{listname} list deleted', 'warning')
    return redirect('/commentlists')

@app.route('/delete/<listname>/<commindex>')
@auth.login_required
def deletecomment(listname, commindex):

    with open('comms.json') as comms:
        commentlists=json.load(comms)
    commentlists[listname].pop(int(commindex))
    with open('comms.json', 'w') as comms: 
        json.dump(commentlists, comms)
    flash('Comment deleted', 'warning')
    return redirect('/commentlists/editlist/'+listname)

@app.route('/commentsbot')
@auth.login_required
def commentsbot():
    indict={}
    try:
        with open('commenttasks.json') as tasks:
            tasksdict=json.load(tasks)
            return render_template('commentsbot.html', tasksdict=tasksdict)
    except:
        with open('commenttasks.json', 'w') as tsks:
            json.dump(indict, tsks)
        with open('commenttasks.json') as tasks:
            tasksdict=json.load(tasks)
            return render_template('commentsbot.html', tasksdict=tasksdict)
@app.route('/commentsbot/newtask', methods=['get','post'])
@auth.login_required
def newtask():
    form=TaskForm()
    with open('comms.json') as comms:
        commentlists=json.load(comms)
    form.commentlist.choices=[(commentlist, commentlist) for commentlist in commentlists]
    accslist=allendswith('auth.json')
    form.account.choices=[(account, account) for account in accslist]
    if form.validate_on_submit():
        return redirect(f'/createtask/{form.channelid.data}&{form.commentlist.data}&{form.numberofcomments.data}&{form.account.data}')
    else: print(form.errors)
    return render_template('newtask.html', form=form)

@app.route('/createtask/<channelid>&<commentlist>&<num>&<acc>')
@auth.login_required
def createtask(channelid, commentlist, num, acc):
    indict={}
    try:
        channelname=getchannelname(channelid)
    except:
        channelname=channelid
    createtask=CommTask(str(uuid1()), channelid, commentlist, num, acc)
    try:
        with open('commenttasks.json') as tasks:
            tasksdict=json.load(tasks)
            task={
                createtask.name:[createtask.channelid, createtask.commentlist, createtask.num, createtask.acc, channelname, '']
            }
            tasksdict.update(task)
            with open('commenttasks.json', 'w') as tasks:
                json.dump(tasksdict, tasks)
    except:
        with open('commenttasks.json', 'w') as tsks:
            json.dump(indict, tsks)
        with open('commenttasks.json') as tasks:
            tasksdict=json.load(tasks)
            task={
                createtask.name:[createtask.channelid, createtask.commentlist, createtask.num, createtask.acc, channelname]
            }
            tasksdict.update(task)
            with open('commenttasks.json', 'w') as tasks:
                json.dump(tasksdict, tasks)
    flash(f'Comment task for {channelname} channel created', 'success')
    
    return redirect('/commentsbot')

@app.route('/commentsbot/deletetask/<task>')
@auth.login_required
def deletetask(task):
    with open('commenttasks.json') as tasks:
        tasksdict=json.load(tasks)
        if tasksdict[task][5] in ['daily', 'every 3 days', 'once every week']:
            apsched.remove_job(str(task)+'scheduler'+str(tasksdict[task][2]))
        del tasksdict[task]
        with open('commenttasks.json', 'w') as tasks:
            json.dump(tasksdict, tasks)
    flash('Task deleted', 'danger')
    return redirect('/commentsbot')

def executenow(task):
    with open('commenttasks.json') as tasks:
        taskdict=json.load(tasks)
        botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
        global backProc
        backProc = multiprocessing.Process(target=botexec.execute, daemon=True)
        backProc.start()
        return taskdict[task][4]

@app.route('/commentsbot/executetask/<task>')
@auth.login_required
def executetasknow(task):
    executedchannelname=executenow(task)
    flash(f'Task for channel {executedchannelname} is running', 'success')
    return redirect('/commentsbot')

@app.route('/scheduletask/day/<task>')
@auth.login_required
def scheduledaily(task):
    with open('commenttasks.json') as tasks:
        taskdict=json.load(tasks)
        botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
        apsched.add_job(func=botexec.execute, trigger='interval', minutes=1, executor='processpool', id=str(task)+'scheduler'+str(taskdict[task][2]))
        taskdict[task][5]='daily'
        with open('commenttasks.json','w') as of:
            json.dump(taskdict, of)
    flash('Task scheduled','success')
    return redirect('/commentsbot')

@app.route('/scheduletask/3days/<task>')
@auth.login_required
def schedule3days(task):
    with open('commenttasks.json') as tasks:
        taskdict=json.load(tasks)
        botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
        apsched.add_job(func=botexec.execute, trigger='interval', days=3, executor='processpool', id=str(task)+'scheduler'+str(taskdict[task][2]))
        taskdict[task][5]='every 3 days'
        with open('commenttasks.json','w') as of:
            json.dump(taskdict, of)
    flash('Task scheduled','success')
    return redirect('/commentsbot')

@app.route('/scheduletask/week/<task>')
@auth.login_required
def scheduleweekly(task):
    with open('commenttasks.json') as tasks:
        taskdict=json.load(tasks)
        botexec=CommTask(task, taskdict[task][0], taskdict[task][1], taskdict[task][2], taskdict[task][3])
        apsched.add_job(func=botexec.execute, trigger='interval', days=7, executor='processpool', id=str(task)+'scheduler'+str(taskdict[task][2]))
        taskdict[task][5]='once every week'
        with open('commenttasks.json','w') as of:
            json.dump(taskdict, of)
    flash('Task scheduled','success')
    return redirect('/commentsbot')

schedulejobs()