"""Task"""
from invoke import task


@task
def makemigrations(cmd, message):
    """Generate alembic migrations"""
    cmd.run(f'alembic revision --autogenerate -m "{message}"')


@task
def migrate(cmd):
    """Execute alembic migrations"""
    cmd.run("alembic upgrade head")
