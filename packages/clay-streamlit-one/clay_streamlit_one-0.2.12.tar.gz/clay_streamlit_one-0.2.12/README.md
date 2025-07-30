## Clay-Streamlit

Are you tired of the boilerplate needed to actually run a useful streamlit app? I was.

* Create multipage apps simply by defining list of pages
* Each page has a name, lambda to show contents, and lambda to show sidebar

* Run your code simply by calling `python <myfile.py>`
* No need to complicate launch.json with `streamlit run <myfile>` commands
* Makes debugging and working in containers simpler

```
from clay_streamlit_one import AppPage, ClayStreamlitApp

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
```