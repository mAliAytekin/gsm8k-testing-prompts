import json
import sqlite3
from .common import canonical, now


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=30)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, metadata TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS records (
            run_id TEXT NOT NULL, question_id TEXT NOT NULL, model_id TEXT NOT NULL,
            condition_id TEXT NOT NULL, demo_pair TEXT NOT NULL, state TEXT NOT NULL,
            record TEXT NOT NULL,
            PRIMARY KEY (run_id,question_id,model_id,condition_id,demo_pair));
        ''')

    def add_run(self, run_id, metadata):
        old = self.db.execute('SELECT metadata FROM runs WHERE id=?', (run_id,)).fetchone()
        if old and json.loads(old[0])['identity'] != metadata['identity']:
            raise ValueError('Run identity collision')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO runs VALUES (?,?)', (run_id, canonical(metadata)))

    def metadata(self, run_id):
        row = self.db.execute('SELECT metadata FROM runs WHERE id=?', (run_id,)).fetchone()
        if not row: raise ValueError('Unknown run ' + run_id)
        return json.loads(row[0])

    @staticmethod
    def key(r):
        return (r['run_id'], r['question_id'], r['model_id'], r['condition_id'], r['demo_pair'])

    def claim(self, r):
        with self.db:
            cursor = self.db.execute('INSERT OR IGNORE INTO records VALUES (?,?,?,?,?,?,?)',
                                     (*self.key(r), 'inflight', canonical(r)))
        return cursor.rowcount == 1

    def save(self, r, state):
        r['updated_at'] = now()
        with self.db:
            self.db.execute('UPDATE records SET state=?,record=? WHERE run_id=? AND question_id=? AND model_id=? AND condition_id=? AND demo_pair=?',
                            (state, canonical(r), *self.key(r)))

    def records(self, run_id):
        return [(state, json.loads(record)) for state, record in self.db.execute(
            'SELECT state,record FROM records WHERE run_id=? ORDER BY rowid', (run_id,))]

    def recover(self, run_id):
        # The request may have reached the server. Do NOT create another sample.
        for state, r in self.records(run_id):
            if state == 'inflight':
                r.update(status='infrastructure_error', error='Interrupted; generation outcome unknown; not resampled', correct=None)
                self.save(r, 'complete')
