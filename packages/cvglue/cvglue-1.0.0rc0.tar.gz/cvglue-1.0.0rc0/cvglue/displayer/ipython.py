from IPython.display import HTML
from base64 import b64encode

__all__ = ["show_mp4"]


def show_mp4(filename, width):
    mp4 = open(filename, 'rb').read()
    data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
    display(HTML("""
    <video width="%d" controls autoplay loop>
        <source src="%s" type="video/mp4">
    </video>
    """ % (width, data_url)))
