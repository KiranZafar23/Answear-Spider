def clean(value):
    return value.replace('\n', '').replace('window.__PRELOADED_STATE__ = ', '')


