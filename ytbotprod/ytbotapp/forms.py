from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, ValidationError, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NoneOf, Regexp, NumberRange
import wtforms_dynamic_fields
import requests
import os
import json
def allendswith(end):
    result=[]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    for root, dirs, files in os.walk(os.path.join(dir_path,"..")): 
        for file in files: 
            if file.endswith(end): 
                result.append(str(file)[:-9])
    return result

class NewList(FlaskForm):
    listname=StringField('List Name', validators=[DataRequired(), Regexp("^[a-zA-Z0-9_]*$")])
    # dynamic=wtforms_dynamic_fields.WTFormsDynamicFields
    # dynamic.add_field('comm', 'Add Comment', TextField)
    submit=SubmitField('Add List')

class NewComm(FlaskForm):
    comment=TextAreaField('New Comment', validators=[DataRequired()])
    submit=SubmitField('Add Comment')


class NewScannerForm(FlaskForm):
    channelid=StringField('Channel ID', validators=[DataRequired(), Length(24,  message="ChannelID must be 24 characters long"), Regexp("^[a-zA-Z0-9_\-]*$")])
    def chancheck(self, channelid):
        r=requests.get(f'https://www.youtube.com/channel/{channelid}')
        if not r.ok:
            raise ValidationError("Invalid Channel ID")
    commentlist=SelectField('Comment List', choices=[])
    account=SelectField('Comment Account', choices=[])
    submit=SubmitField('Scan Channel')

class AccountForm(FlaskForm):
    accountname=StringField('Account Name', validators=[DataRequired(), NoneOf(allendswith('auth.json')), Regexp("^[a-zA-Z0-9_\-]*$") ])
    code=StringField('Authentication Code', validators=[DataRequired()])
    submit=SubmitField('Add Account')

class TaskForm(FlaskForm):
    indict=dict()
    try:
        with open('commenttasks.json') as tasks:
            tasksdict=json.load(tasks)
    except:
        with open('commenttasks.json', 'w') as tsks:
            json.dump(indict, tsks)
        with open('commenttasks.json') as tasks:
            tasksdict=json.load(tasks)
    #name=StringField('Task Name', validators=[DataRequired(),NoneOf(tasksdict.keys()), Regexp("^[a-zA-Z0-9_\-\ ]*$")])
    channelid=StringField('Channel ID', validators=[DataRequired(), Length(24,  message="ChannelID must be 24 characters long"), Regexp("^[a-zA-Z0-9_\-]*$")])
    numberofcomments=IntegerField('Number of comments', validators=[DataRequired(), NumberRange(min=1, max=35)])
    commentlist=SelectField('Comment List', choices=[])
    account=SelectField('Comment Account', choices=[])
    submit=SubmitField('Create Task')
    def chancheck(self, channelid):
        r=requests.get(f'https://www.youtube.com/channel/{channelid}')
        if not r.ok:
            raise ValidationError("Invalid Channel ID")