# run.py
# main entry point for the user service

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)