
from clay_streamlit_one import AppPage

def test_app_page_creation():
    page = AppPage("Test Page")
    assert page.name == "Test Page"
    assert page.main_fun is None
    assert page.sidebar_fun is None



