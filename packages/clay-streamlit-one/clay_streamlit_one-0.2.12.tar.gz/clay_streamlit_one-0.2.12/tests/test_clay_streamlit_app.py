
from clay_streamlit_one import ClayStreamlitApp


def test_clay_streamlit_app_creation():
    app = ClayStreamlitApp("Test App")
    assert app.name == "Test App"
    assert app.pages_dict == {}
    assert app.app_sidebar_fun is None