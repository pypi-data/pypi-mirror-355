import json
import logging
import os
import random
import sys
import traceback
from collections import OrderedDict
from pathlib import Path

import streamlit as st
from streamlit import runtime
from streamlit.web import cli as stcli

# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clay_streamlit_one import AppPage
from clay_streamlit_one import __version__ as clay_st_version

# a bunch of defaults
DEFAULT_PORT = 9988
DEFAULT_APP_NAME = "mi aplicación"
DEFAULT_ICONS = [":feet:", ":eye:", ":eyes:", ":ear:", ":lips", ":tongue:", ":shark:", ":dvd:"]

class ClayStreamlitApp():
    
    def __init__(self, 
                 name=None, 
                 page_icon=None, 
                 port=None, 
                 app_sidebar_fun = None, 
                 settings_filename="settings.json", 
                 version_str=None, 
                 logofile=None
                ):
        
        self.name = name or DEFAULT_APP_NAME
        self.page_icon  = page_icon or random.choice(DEFAULT_ICONS)
        self.port = port or DEFAULT_PORT
        self.app_sidebar_fun = app_sidebar_fun
        self.settings_filename = settings_filename
        if version_str is not None:
            self.version_str = version_str
        else:
            self.version_str = clay_st_version
        
        self.exception_handler = self.built_in_exception_handler

        self.pages_dict = {}
        self.logo_file = logofile

    def _force_quit(self):
        pid = os.getpid()
        logging.info(f"-- Sending (kill -9) to pid {pid} --")
        os.kill(pid, 9)  # Forcefully stops the server        

    def built_in_exception_handler(self, e):
            error_str = f"### :wrench: An error was caught: {e}\n"
            levels = get_stacktrace_from_exception(e)
            stack_str = f"Last {len(levels)} levels of stack trace:"
            levels_str = "\n* " + "\n* ".join(levels)
            
            try:
                self.my_error.error(f"{error_str}  {stack_str}  {levels_str}")
                with st.expander(":red[**There was an error**. Click for details.]", expanded=False):
                    st.warning(":wrench: Critical Error :bomb:")

                    st.error(f"{error_str}  {stack_str}  {levels_str}")
            except Exception as e2:
                st.error(f"oh my, another error, {e2}")
                pass

            logging.error(f"Exception occurred: {e.__class__.__name__}: {e}. Traceback: \n* {levels_str}\n---\n")

    def run(self):
        if runtime.exists():
            try:
                main_error, buttons, page_to_run = self.setup_page()
                
                st.session_state["clayst_JSON_SETTINGS_NAME"] = self.settings_filename
                del self.settings_filename
                self.default_settings, updated = load_defaults()
                
                self.run_page(page_to_run) 
            
            except Exception as e:
                self.exception_handler(e)
    
        else:
            logging.info ("no streamlit found, relaunching with streamlit")
            sys.argv = ["streamlit", "run",
                        sys.argv[0], "--server.port", str(self.port), "--browser.serverAddress" , "localhost" ]

            retval = stcli.main()
            sys.exit(retval)

    def set_pages(self, pages_array):
        self.pages_dict = OrderedDict()
        for p in pages_array:
            self.pages_dict[ p.name ] =  p 

    def add_page(self, page):
        self.pages[page.name] = page


    def init_streamlit_page(self):
        # sets up icon, wide layout, title
        st.set_page_config(
                page_title=self.name,
                page_icon=self.page_icon,
                layout="wide",
            )
        
        hide_streamlit_footer_css = """
                <style>
                    #MainMenu1 { 
                        visibility: hidden;
                        }
                    footer {
                        visibility: hidden;
                        }
                </style>
            """
        st.markdown(hide_streamlit_footer_css, unsafe_allow_html=True)

        
    def setup_page(self):
        self.init_streamlit_page()
        ## always initializes the page with sidebar, error placeholder empty().container()
        self.sidebar = st.sidebar.empty().container() 
        self.my_error = st.container()

        with self.sidebar:
            if self.logo_file is not None:
                try:
                    # logo requires streamlit>=1.35, not always available. 
                    st.logo(self.logo_file)
                except:
                    st.image(self.logo_file,  width=100)
            html_content = f"""
                <div style="border:0.5px dashed blue; border-radius: 5px; font-size:12px; padding: 10px">
                    {self.name}, version {self.version_str}
                </div>
                """
            # Use the Markdown method to render the HTML content
            st.markdown(html_content, unsafe_allow_html=True)


            if len(self.pages_dict) == 0:
                raise Exception("No pages found - App must have at least one Page")
             
            elif len(self.pages_dict) == 1:     
                # no need to list pages on sidebar, just run the single page
                s1 = list(self.pages_dict.keys())[0]     
                # st.divider()
                st.write(f"**{s1}**")
            
            else:
                s1 = st.selectbox(label=":blue[**Select Page**]", 
                        options=self.pages_dict.keys(), key="app_page")                
                     
            if self.app_sidebar_fun is not None:
                self.app_sidebar_fun()
                
        return self.my_error, self.sidebar, s1
            
    def run_page(self, page_to_run):

        page_object = self.pages_dict[page_to_run]
        
        msg = f"""{self.page_icon} {self.name}\\
            :blue[version {self.version_str}]"""
        show_toast(msg)

        with self.sidebar:
            page_object.set_sidebar()
        

        page_object.run()
    
def get_settings_file_path():
    settings_file_name = st.session_state.get("clayst_JSON_SETTINGS_NAME", "settings.json")
    return Path.cwd() / settings_file_name

# Function to load the default values from the JSON file
def load_defaults():
    updated = False
    data = {}
    settings_file = "UNDEFINED"
    try:
        settings_file = get_settings_file_path()
        with open(settings_file, "r") as f:
            data = json.load(f)
            if len(data) == 0:
                logging.debug(f"Loaded ClayStreamlitApp defaults file, no entries found. Loc '{settings_file}'")
            else:
                # strs = []
                for k, v in data.items():
                    if k not in st.session_state and v != "":
                        updated = True
                        st.session_state[k] = v
                        # strs.append(f"   {k:30}  -->  {v}")
                logging.info(f"Loaded ClayStreamlitApp defaults file with {len(data)} entries")

    except FileNotFoundError:
        return {}, updated
    except json.JSONDecodeError as jde:
        logging.error(f"Failed to load ClayStreamlitApp defaults, JSONDecodingError is {jde}")
        return {}, updated


    return data, updated

def update_defaults_entry(key, value):
    settings_file = get_settings_file_path()
    try:
        with open(settings_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError as jde:
        data = {}


    data[key] = value
    try:
        with open(settings_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.warning(f"Failed to update settings file, for key {key}")

def show_toast(msg):
    # sorry, st.cache_data didn't work for making this one-time, had to do it using session_state. yikes.
    if "TOAST_ALREADY_SHOWN" in st.session_state:
        return False
    else:
        try:
            st.session_state["TOAST_ALREADY_SHOWN"] = 1
            st.toast(msg)
        except:
            pass
        return True

def get_stacktrace_from_exception(e: Exception, num_levels=10):

    # Extract the stack trace
    stack_trace = traceback.extract_tb(e.__traceback__)

    # Print the top 2 stack traces
    levels = list()
    for trace in stack_trace[-num_levels:]:
        levels.append(f"File: {trace.filename}, Line: {trace.lineno}, Function: {trace.name}, Code: {trace.line}")
    
    return levels
        

if __name__ == "__main__":
   
    demo_code = """
    ## DEMO CODE ##

    #                                                                            #
    ## Simplest way to use this library. You can run this as python <file.py>   ##
    ##          no need to call streamlit directly                              ##

    import streamlit as st
    from clay_streamlit import AppPage, ClayStreamlitApp


    pages_list = [
            AppPage.AppPage("first page", None, lambda: st.button("This is a button for the first page") ),
            AppPage.AppPage("Hi", lambda: st.code(demo_code) and st.write("Success! ClayStreamlitApp is working")),
            ]

    myapp = ClayStreamlitApp.ClayStreamlitApp()
    myapp.set_pages(pages_list)
    myapp.run()
    """
    
    pages_list = [
        AppPage.AppPage("first page", 
            None, 
            lambda: st.button("This is a button for the first page") 
        ),
        AppPage.AppPage("Hi", 
            lambda: st.code(demo_code) and st.write("Success! ClayStreamlitApp is working"),
            None
        ),
    ]
    myapp = ClayStreamlitApp.ClayStreamlitApp()
    myapp.set_pages(pages_list)
    myapp.run()