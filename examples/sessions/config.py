config = {}

config['tipfy'] = {
    'middleware': [
        # Enable debugger. It will be loaded only in development.
        'tipfy.ext.debugger.DebuggerMiddleware',
    ],
}

config['tipfy.ext.session'] = {
    # Change this!!!
    'secret_key': 'my_strong_secret_key',
}
