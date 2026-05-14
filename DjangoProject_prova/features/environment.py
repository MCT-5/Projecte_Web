from splinter import Browser


def before_all(context):
    context.browser = Browser('django')


def after_all(context):
    context.browser.quit()
