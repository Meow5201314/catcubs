from app import create_app, db
from app.models import User, Post, Comment, PostView

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Comment': Comment, 'PostView': PostView}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
