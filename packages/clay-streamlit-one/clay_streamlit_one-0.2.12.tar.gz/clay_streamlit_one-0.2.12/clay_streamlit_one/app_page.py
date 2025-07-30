import os
import streamlit as st
import time
import logging


class AppPage():
    def __init__(self, name, main_fun=None, sidebar_fun=None):
        # log the creation of the page
        self.name = name
        
        self.main_fun = main_fun
        self.sidebar_fun = sidebar_fun
        # log the creation if main_fun and/or sidebar_fun are None
        if main_fun is None and sidebar_fun is None:
            logging.info(f"Creating AppPage {name} with no main_function nor sidebar_function")
        elif main_fun is None:
            logging.info(f"Creating AppPage {name} with no main_function")
        elif sidebar_fun is None:
            logging.info(f"Creating AppPage {name} with no sidebar_function")
        
    def run(self):
        if self.main_fun is None:
            print(f"AppPage.run called for page '{self.name}'")
            st.header(f"Add Code for Page '{self.name}' here")
        else:
            self.main_fun()

    # this is called by ClayStreamlitApp.run_page
    def set_sidebar(self):
        if self.sidebar_fun is not None:
            st.write(f":rainbow[*menus for {self.name}*]", unsafe_allow_html=True)
            self.sidebar_fun()


    def _force_quit(self):
        pid = os.getpid()
        st.error(f"**The app was terminated on page {self.name}**")
        logging.info(f"The app was terminated on page {self.name}**")
        time.sleep(0.1)
        os.kill(pid, 9)  # Forcefully stops the server        
        
