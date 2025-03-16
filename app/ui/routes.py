"""
EchoForge - UI Routes

This module defines the user interface routes for the EchoForge application.
"""

import logging
import os
from flask import Blueprint, render_template, redirect, url_for, current_app, request, flash, jsonify

# Set up logging
logger = logging.getLogger("echoforge.ui")

# Create UI blueprint
ui_bp = Blueprint("ui", __name__)

def register_ui_routes(app):
    """Register the UI routes with the Flask application."""
    app.register_blueprint(ui_bp)

# UI Routes
@ui_bp.route("/")
def index():
    """Render the main page."""
    return render_template("index.html", title="EchoForge - AI Character Voice Creation")

@ui_bp.route("/voices")
def voices():
    """Render the voices page."""
    return render_template("voices.html", title="Voice Library - EchoForge")

@ui_bp.route("/create")
def create():
    """Render the character creation page."""
    return render_template("create.html", title="Create Character - EchoForge")

@ui_bp.route("/generate")
def generate():
    """Render the speech generation page."""
    return render_template("generate.html", title="Generate Speech - EchoForge")

@ui_bp.route("/dashboard")
def dashboard():
    """Render the admin dashboard page."""
    return render_template("dashboard.html", title="Dashboard - EchoForge")

@ui_bp.route("/docs")
def docs():
    """Render the documentation page."""
    return render_template("docs.html", title="Documentation - EchoForge")

@ui_bp.route("/about")
def about():
    """Render the about page."""
    return render_template("about.html", title="About - EchoForge") 