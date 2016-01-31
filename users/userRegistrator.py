__author__ = 'slash'
from flask import Request, Response
from model_cloudcalc import Base, User, User_action
from sqlalchemy.orm.exc import NoResultFound
import datetime

class UserSession:
    ''' Class for work with session of the particular user
    '''
    TOKEN = 'userToken'
    TOKEN_LIFETIME = 60         # 60 days
    KEY = 'sessionKey'

    def __init__(self, dbSession, request):
        user_cookie = request.cookies.get(UserSession.TOKEN)
        exists = False
        if (user_cookie):       # user exists
            try:           # try to find user in database
                user = dbSession.query(User).filter(User.cookie == user_cookie).one()
                exists = True
            except NoResultFound as e:
                user = User()           # create new 'dummy' user

        else:                   # user doesn't exist - create new user entry
            user = User()
        # get connection IP-address
        ip = request.remote_addr
        if (not exists):
            user.userdata = {'ip' : ip}
            dbSession.add(user)
            dbSession.commit()

        # save user parameters for future use
        self.user_cookie = user.cookie      # save user cookie for future use !!!
        self.user_id = user.id
        self.user = user
        # If user doesn't exist - fill all parameters and save
        # If user didn't exist - fix registration event
        self.toSetKey = False
        if (not exists):
            event = User_action(user.id, User_action.REGISTER, ip, False)
            dbSession.add(event)
            dbSession.commit()
            self.toSetKey = True
        else:
            # Check for session key
            session_key = request.cookies.get(UserSession.KEY)
            if (not session_key):
                event = User_action(user.id, User_action.CONNECT, ip, True)
                dbSession.add(event)
                dbSession.commit()
                self.toSetKey = True
        # User is now in database, event registered


    def registerEvent(self, dbSession, action, request, data=None):
        '''
        :param dbSession: DB session
        :param action: event type to register (from User_action class definition)
        :param request: request object (to get IP and more info in the future)
        :param data: additional data
        :return:
        '''
        event = User_action(self.user_id, action, request.remote_addr, True)
        if (data):
            event.data = data
        dbSession.add(event)
        dbSession.commit()
        return True


    def setCookies(self, response):
        '''
        :param response: prepared response object
        :return: set required cookies to response object
        '''
        cookieEndTime = datetime.datetime.now() + datetime.timedelta(days=UserSession.TOKEN_LIFETIME) # 60 days in future
        response.set_cookie(UserSession.TOKEN, self.user_cookie, expires=cookieEndTime)         # set tracking cookie
        if self.toSetKey:
            response.set_cookie(UserSession.KEY, '1')      # If user just came - set session key True.

        return True

    def getCookie(self):
        return self.user_cookie

    def getUserID(self):
        return self.user_id

