import logging,os,os.path,sqlite3,time
from pathlib import Path
from localstack.config import is_in_docker
from localstack.utils.strings import short_uid
from eventstudio import config
LOG=logging.getLogger(__name__)
def get_database_directory()->Path:
	if is_in_docker:A=Path('/var/lib/localstack/state/extensions/eventstudio')
	else:A=config.PACKAGE_ROOT
	if not A.is_dir():A.mkdir(parents=True)
	B=A/config.DATABASE_NAME;LOG.info(f"Database path: {B}");return B
def clear_db():
	A=get_database_directory()
	if not config.PERSISTENCE and os.path.exists(A):os.remove(A);LOG.info('EventStudio database removed')
def check_and_close_sqlite_db(db_path:Path,max_attempts=10,wait_time=5):
	B=wait_time;A=db_path
	if not os.path.isfile(A):return A
	for D in range(max_attempts):
		try:
			with sqlite3.connect(A,timeout=1,isolation_level='IMMEDIATE'):print(f"Successfully opened {A}");return A
		except sqlite3.OperationalError as C:
			if'database is locked'in str(C):print(f"Attempt {D+1}: Database is locked. Waiting {B} seconds...");time.sleep(B)
			else:print(f"An operational error occurred: {C}")
	return A+short_uid()