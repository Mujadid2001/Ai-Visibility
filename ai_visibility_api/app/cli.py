"""CLI commands for Flask app."""
import click
from flask.cli import with_appcontext
from app import db


@click.command("init-db")
@with_appcontext
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo("Database initialized!")


@click.command("drop-db")
@with_appcontext
def drop_db():
    """Drop all tables (WARNING: loses all data)."""
    if click.confirm("⚠️  This will delete all data. Continue?"):
        db.drop_all()
        click.echo("Database dropped!")
    else:
        click.echo("Cancelled.")


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    """Seed database with demo data."""
    from app.models import BusinessProfile
    
    if BusinessProfile.query.filter_by(domain="surferseo.com").first():
        click.echo("Demo data already exists!")
        return
    
    demo_profile = BusinessProfile(
        name="Surfer SEO",
        domain="surferseo.com",
        industry="SEO Software",
        description="AI-powered SEO content optimization tool",
        competitors=["clearscope.io", "marketmuse.com", "frase.io"],
        status="active",
    )
    
    db.session.add(demo_profile)
    db.session.commit()
    click.echo(f"✓ Created demo profile: {demo_profile.uuid}")


def register_cli(app):
    """Register CLI commands with Flask app."""
    app.cli.add_command(init_db)
    app.cli.add_command(drop_db)
    app.cli.add_command(seed_demo)
