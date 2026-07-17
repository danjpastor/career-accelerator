\
"""Saved submission and progress helpers for applied analytics labs."""
from __future__ import annotations
from datetime import date
import os, shutil, subprocess, sys
from pathlib import Path
from career_app.data.applied_exercises import APPLIED_EXERCISES

VALID_STATUSES = ("Not Started", "In Progress", "Completed")

def exercise(number):
    number = int(number)
    if number not in APPLIED_EXERCISES:
        raise ValueError(f"Applied Lab {number:02d} is not in the catalog.")
    return APPLIED_EXERCISES[number]

def paths(root, number):
    item = exercise(number); practice = Path(root)/'practice/applied'; d = practice/'exercises'/item['slug']
    return {'practice_root':practice,'exercise_dir':d,'instructions':d/'README.md','starter':d/item['starter_filename'],'validation':d/'validation.md','datasets':practice/'datasets'/item['dataset_slug'],'submissions':practice/'submissions'}

def submission_path(root, number):
    item = exercise(number); suffix = Path(item['starter_filename']).suffix
    return paths(root,number)['submissions']/f"{int(number):02d}_{item['slug']}{suffix}"

def _template(root, number):
    item = exercise(number); starter = paths(root,number)['starter']; text = starter.read_text(encoding='utf-8')
    if starter.suffix == '.py': header=f"# Career Accelerator Applied Lab {int(number):02d}\n# {item['title']}\n\n"
    elif starter.suffix == '.sql': header=f"-- Career Accelerator Applied Lab {int(number):02d}\n-- {item['title']}\n\n"
    else: header=f"<!-- Career Accelerator Applied Lab {int(number):02d}: {item['title']} -->\n\n"
    return header+text

def ensure_submission(root, number):
    path=submission_path(root,number); path.parent.mkdir(parents=True,exist_ok=True); created=not path.exists()
    if created: path.write_text(_template(root,number),encoding='utf-8')
    return path,created

def submission_has_changes(root, number):
    path=submission_path(root,number)
    return path.exists() and path.read_text(encoding='utf-8').replace('\r\n','\n').strip()!=_template(root,number).replace('\r\n','\n').strip()

def _task_rows(conn, number):
    item=exercise(number); labels=[item['label'],*item.get('aliases',[])]; marks=','.join('?' for _ in labels)
    return conn.execute(f"SELECT s.id,s.completed,m.status FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id WHERE s.label IN ({marks})",tuple(labels)).fetchall()

def progress(conn, root, number):
    item=exercise(number); row=conn.execute('SELECT * FROM applied_exercise_progress WHERE exercise_number=?',(int(number),)).fetchone(); status=row['status'] if row else 'Not Started'; notes=row['notes'] if row and row['notes'] else ''; completed_date=row['completed_date'] if row else None; saved=row['submission_path'] if row and row['submission_path'] else None
    tasks=_task_rows(conn,number)
    if any(bool(t['completed']) or t['status']=='Completed' for t in tasks): status='Completed'
    elif status=='Not Started' and any(t['status']=='In Progress' for t in tasks): status='In Progress'
    path=submission_path(root,number)
    if path.exists(): saved=str(path.relative_to(Path(root))).replace('\\','/')
    return {'number':int(number),'title':item['title'],'status':status,'notes':notes,'completed_date':completed_date,'submission_path':saved,'submission_exists':path.exists(),'submission_changed':submission_has_changes(root,number) if path.exists() else False,'task_ids':[int(t['id']) for t in tasks]}

def save_progress(conn, root, number, *, status, notes=''):
    if status not in VALID_STATUSES: raise ValueError(f'Unsupported status: {status}')
    item=exercise(number); path=submission_path(root,number); rel=str(path.relative_to(Path(root))).replace('\\','/') if path.exists() else None; completed_date=date.today().isoformat() if status=='Completed' else None
    conn.execute("""INSERT INTO applied_exercise_progress(exercise_number,status,submission_path,notes,completed_date,updated_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(exercise_number) DO UPDATE SET status=excluded.status,submission_path=excluded.submission_path,notes=excluded.notes,completed_date=excluded.completed_date,updated_at=CURRENT_TIMESTAMP""",(int(number),status,rel,str(notes or ''),completed_date))
    completed=status=='Completed'
    for task in _task_rows(conn,number):
        tid=int(task['id']); conn.execute('UPDATE sprint_tasks SET completed=? WHERE id=?',(1 if completed else 0,tid)); conn.execute("UPDATE task_metadata SET status=?,prerequisite_state='Ready',prerequisite_reason=NULL WHERE task_id=?",(status,tid))
    source=f"Applied Lab {int(number):02d}: {item['title']}"
    if completed:
        desc=f"Completed a guided {item['category']} lab demonstrating {item['concepts']}."+(f" Submission: {rel}" if rel else '')
        conn.execute("""INSERT INTO evidence(skill,source_type,source_name,description) VALUES(?,?,?,?) ON CONFLICT(skill,source_type,source_name) DO UPDATE SET description=excluded.description""",(item['evidence_skill'],item['source_type'],source,desc))
    else: conn.execute('DELETE FROM evidence WHERE source_name=?',(source,))
    conn.commit(); return progress(conn,root,number)

def open_folder(path):
    path=Path(path).resolve()
    if not path.exists(): raise FileNotFoundError(path)
    if os.name=='nt': os.startfile(str(path)); return 'File Explorer'
    if sys.platform=='darwin': subprocess.Popen(['open',str(path)]); return 'Finder'
    cmd=shutil.which('xdg-open')
    if cmd: subprocess.Popen([cmd,str(path)]); return 'the file manager'
    raise RuntimeError('No supported folder-opening command was found.')
