EXT_TO_MIME = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.swf': 'application/x-shockwave-flash',
}
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: 'Bad_Request',
    FORBIDDEN: 'Forbidden',
    NOT_FOUND: 'Not_Found',
    METHOD_NOT_ALLOWED: 'Method_Not_Allowed',
    INVALID_REQUEST: 'Invalid_Request',
    INTERNAL_ERROR: 'Internal_Server_Error',
}

ALLOWED_METHODS = ['HEAD', 'GET']
INDEX_FILE = 'index.html'
ERROR_MSG_TEMPLATE = error_message = '''
    <!doctype html>
    <html lang='ru'>
    <head>
      <meta charset='utf-8' />
      <title>ERROR</title>
    </head>
    <body>
        <h1>{}</h1>
        <p>{}</p>
    </body>
    </html>
'''
