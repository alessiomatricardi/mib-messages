class Config(object):
    DEBUG = False
    TESTING = False

    import os

    REQUESTS_TIMEOUT_SECONDS = float(os.getenv("REQUESTS_TIMEOUT_SECONDS", 5))

    # users microservice
    USERS_MS_PROTO = os.getenv('USERS_MS_PROTO', 'http')
    USERS_MS_HOST = os.getenv('USERS_MS_HOST', 'localhost')
    USERS_MS_PORT = os.getenv('USERS_MS_PORT', 5001)
    USERS_MS_URL = '%s://%s:%s' % (USERS_MS_PROTO, USERS_MS_HOST, USERS_MS_PORT)

    # blacklist microservice
    BLACKLIST_MS_PROTO = os.getenv('BLACKLIST_MS_PROTO', 'http')
    BLACKLIST_MS_HOST = os.getenv('BLACKLIST_MS_HOST', 'localhost')
    BLACKLIST_MS_PORT = os.getenv('BLACKLIST_MS_PORT', 5002)
    BLACKLIST_MS_URL = '%s://%s:%s' % (BLACKLIST_MS_PROTO, BLACKLIST_MS_HOST, BLACKLIST_MS_PORT)


class DebugConfig(Config):
    """
    This is the main configuration object for application.
    """
    DEBUG = True
    TESTING = False

    SECRET_KEY = b'isreallynotsecretatall'

    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../db.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class DevConfig(DebugConfig):
    """
    This is the main configuration object for application.
    """
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../messages_ms.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    """
    This is the main configuration object for application.
    """
    TESTING = True

    import os
    SECRET_KEY = os.urandom(24)
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../messages_ms.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProdConfig(DevConfig):
    """
    This is the main configuration object for application.
    """
    TESTING = False
    DEBUG = False

    import os
    SECRET_KEY = os.getenv('APP_SECRET', os.urandom(24))

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTGRES_USER = os.getenv('POSTGRES_USER', None)
    POSTGRES_PASS = os.getenv('POSTGRES_PASSWORD', None)
    POSTGRES_DB = os.getenv('POSTGRES_DB', None)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', None)
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    SQLALCHEMY_DATABASE_URI = 'postgres://%s:%s@%s:%s/%s' % (
        POSTGRES_USER, POSTGRES_PASS, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

