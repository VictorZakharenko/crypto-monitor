from app import create_app, db
from app.models import Manager, Company, User

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Manager': Manager, 'Company': Company, 'User': User}


