"""
UI Tests for EchoForge web interface.

This module contains tests for the EchoForge web interface pages.
"""

import os
import pytest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup

from app.main import app

# Create test client
client = TestClient(app)

class TestUIPages:
    """Tests for the EchoForge web interface pages."""
    
    def test_index_page(self):
        """Test that the index page loads correctly."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check title
        assert "EchoForge" in soup.title.text
        
        # Check navigation
        nav_links = soup.select("nav ul li a")
        assert len(nav_links) >= 3
        
        # Check for theme toggle button
        theme_toggle = soup.select_one("#theme-toggle")
        assert theme_toggle is not None
    
    def test_generate_page(self):
        """Test that the generate page loads correctly."""
        response = client.get("/generate")
        assert response.status_code == 200
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check title
        assert "EchoForge" in soup.title.text
        
        # Check for form elements - using the actual IDs from the template
        form = soup.select_one("form#generation-form")
        assert form is not None
        
        # Check for text input
        text_input = soup.select_one("textarea#text-input")
        assert text_input is not None
        
        # Check for character select
        character_select = soup.select_one("select#character-select")
        assert character_select is not None
        
        # Check for navigation
        nav_links = soup.select("nav ul li a")
        assert len(nav_links) >= 3
        
        # Check for active link
        active_link = soup.select_one("nav ul li a.active")
        assert active_link is not None
        assert "Generate" in active_link.text
    
    def test_characters_page(self):
        """Test that the characters page loads correctly."""
        response = client.get("/characters")
        assert response.status_code == 200
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check title
        assert "EchoForge" in soup.title.text
        assert "Character" in soup.title.text
        
        # Check for filter controls
        gender_filter = soup.select_one("#gender-filter")
        assert gender_filter is not None
        
        style_filter = soup.select_one("#style-filter")
        assert style_filter is not None
        
        search_filter = soup.select_one("#search-filter")
        assert search_filter is not None
        
        # Check for character grid
        character_grid = soup.select_one("#character-grid")
        assert character_grid is not None
        
        # Check for character card template
        card_template = soup.select_one("#character-card-template")
        assert card_template is not None
        
        # Check for modal
        modal = soup.select_one("#character-modal")
        assert modal is not None
    
    def test_dark_mode_support(self):
        """Test that pages support dark mode via data-theme attribute."""
        # Test index page
        response = client.get("/")
        soup = BeautifulSoup(response.text, 'html.parser')
        html_tag = soup.find("html")
        assert "data-theme" in html_tag.attrs
        
        # Test generate page
        response = client.get("/generate")
        soup = BeautifulSoup(response.text, 'html.parser')
        html_tag = soup.find("html")
        assert "data-theme" in html_tag.attrs
        
        # Test characters page
        response = client.get("/characters")
        soup = BeautifulSoup(response.text, 'html.parser')
        html_tag = soup.find("html")
        assert "data-theme" in html_tag.attrs
    
    def test_api_health_endpoint(self):
        """Test that the API health endpoint returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_api_voices_endpoint(self):
        """Test that the API voices endpoint returns a list."""
        response = client.get("/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # In test mode, we should get mock voices
        if os.environ.get("ECHOFORGE_TEST") == "true" or len(data) > 0:
            # Check first voice has required fields
            first_voice = data[0]
            assert "speaker_id" in first_voice
            assert "name" in first_voice
            assert "gender" in first_voice 