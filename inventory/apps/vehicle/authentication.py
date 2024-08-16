import json
from functools import lru_cache

import jwt
import requests
from decouple import config
from jwt.algorithms import RSAAlgorithm
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


region = config("COGNITO_REGION")
user_pool_id = config('COGNITO_USER_POOL_ID')
client_id = config('COGNITO_CLIENT_ID')
issuer = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}'


@lru_cache(maxsize=1)
def get_jwks():
    jwks_url = f'{issuer}/.well-known/jwks.json'
    response = requests.get(jwks_url)
    response.raise_for_status()
    return response.json()


def validate_token(token):
    jwks = get_jwks()

    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header['kid']

    key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
    if not key:
        raise ValueError('Public key not found')

    public_key = RSAAlgorithm.from_jwk(json.dumps(key))

    try:
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=client_id,
            issuer=issuer,
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidAudienceError:
        raise ValueError('Token was not issued for this audience')
    except jwt.InvalidIssuerError:
        raise ValueError('Token issuer is invalid')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None

        try:
            token = authorization_header.split('Bearer ')[1]
            decoded_token = validate_token(token)
            user_id = decoded_token['sub']
            return (user_id, None)
        except Exception:
            raise AuthenticationFailed('Invalid token')

    def authenticate_header(self, request):
        return 'Bearer'
