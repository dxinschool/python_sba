from flask import Flask

import config
import database
import models
from routes import auth, candidate_panel, teacher, voting

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.context_processor
def shared_template_values():
    return {
        'title': config.ELECTION_TITLE,
        'deadline': models.setting('election_deadline', config.DEFAULT_DEADLINE),
    }


app.teardown_appcontext(database.close_db)

for blueprint in (auth.bp, voting.bp, teacher.bp, candidate_panel.bp):
    app.register_blueprint(blueprint)

# Create election.db and fill it with sample data on the very first run.
database.init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
