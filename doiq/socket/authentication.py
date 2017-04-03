from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication
import logging

class SocketJWTAuthentication(BaseJSONWebTokenAuthentication):

    def get_jwt_value(self, tokenJWT):
        return tokenJWT
