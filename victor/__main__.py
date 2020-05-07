import sys

def qt_main():
    from .qt_app import QTVictorApplication
    app = QTVictorApplication()

    return_code = app.run()
    sys.exit(return_code)

if __name__ == '__main__':
    qt_main()
