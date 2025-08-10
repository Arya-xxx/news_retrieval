from app import create_app
from app.controllers import news_controller

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)