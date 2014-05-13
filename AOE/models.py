from django.contrib.auth.models import User
from django.db import models
from django.utils import safestring
from django.utils.encoding import smart_str
from testtools import safeExec
import random
import testtools
import traceback

# Create your models here.

class Topic(models.Model):
    slug = models.SlugField(unique=True)
    def title(self):
        splt = self.slug.split('-')
        return u' '.join(i.title() for i in splt)
    def __repr__(self):
        return self.title()
    def __unicode__(self):
        return self.title()
    @models.permalink
    def get_absolute_url(self):
        return ('topic_detail', (), {'slug':self.slug})

class Question(models.Model):
    question = models.TextField()
    answer = models.TextField(default='')
    topic = models.ForeignKey(Topic)
    why = models.TextField(default='', blank=True)
    safeFunctions = models.CharField(max_length=1024, default='', blank=True)
    qid = models.SmallIntegerField(default=0)
    #funcname = models.TextField(max_length=32, default='func')
    def __unicode__(self):
        s = str(self.question)
        return unicode(s[:s.index('.')])
    @models.permalink
    def get_absolute_url(self):
        return ('question_detail', (), {'qid':self.qid, 'slug':self.topic.slug})
    def check(self, response, d={'randomlist':testtools.randomlist, 'randint':random.randint}):
        safefunctions = self.smartstr(self.safeFunctions).split(' ')
        if safefunctions == ['']:
            safefunctions = []
        sucess, message, local = safeExec(self.smartstr(response), safefunctions)
        if sucess:
            local.update(d)
            try:
                exec self.smartstr(self.answer) in {}, local
                sucess = True
            except:
                message = traceback.format_exc()
                sucess = False
        return sucess, message
    def smartstr(self, s):
        return smart_str(''.join(c for c in s if c!='\r'))
    #class Meta:
        #unique_together = (topic, qid)
    def save(self):
        self.qid = self.topic.question_set.count()+1
        super(Question, self).save()
    def delete(self):
        for quest in self.topic.question_set.filter(qid__gt=self.qid):
            quest.qid -= 1 
        super(Question, self).delete()
    def next(self):
        'returns the next question or raises DoesNotExist'
        return self.topic.question_set.get(qid=self.qid+1)
    def topic_name(self):
        return unicode(self.topic) + ' ' + unicode(self)

#class EvalQuestion(Question):
#    def check(self, response):
#        raise Exception("Not implemented...        s")
#        return str(eval(response, {'__builtins__':None}, {})) == str(self.answer)        
#
#class UnitTestQuestion(Question):
#    pass

class UserProfile(models.Model):
    score = models.IntegerField(default=0)
    user = models.OneToOneField(User, primary_key=True)
    
class QuestionUser(models.Model):
    score = models.IntegerField(default=0)
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question)
    def __unicode__(self):
        return self.question.__unicode__()

class Response(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    response = models.TextField()
    score = models.IntegerField(default=0)
    question_user = models.ForeignKey(QuestionUser)
    class Meta:
        get_latest_by = 'date'
    def table_row(self):
        try:
            fields = ['date' ,'response', 'user_question__question__topic_name', 'score']
            print [['<td>', getattr(self, i), '</td>'] for i in fields]
            return ''.join([''.join(['<td>', getattr(self, i),'</td>']) for i in fields])
        except Exception, e:
            return e
