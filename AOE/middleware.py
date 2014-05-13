'''
Created on Mar 6, 2011

@author: aoeu
'''

class Middleware(object):
    """
    Middleware that handles temporary messages.
    """

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        """
        Updates the storage backend (i.e., saves the messages).

        If not all messages could not be stored and ``DEBUG`` is ``True``, a
        ``ValueError`` is raised.
        """
        pass