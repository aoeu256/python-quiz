'''
Created on Feb 18, 2011

@author: aoeu
'''

from django.contrib import admin
from testdjango.elearn.models import Question, Response, Topic, UserProfile

  

for i in [Response, Topic, UserProfile, Question]:
    admin.site.register(i)