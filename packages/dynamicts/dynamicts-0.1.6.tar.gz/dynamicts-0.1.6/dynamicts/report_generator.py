import base64
import io
from datetime import datetime
import os

def log_plot_to_md_report(fig, title, data_filepath):
    """
    Logs a matplotlib figure to a Markdown report file, saving in a directory based on the data file name.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure to be saved.
    title : str
        The title for the plot section in the report.
    data_filepath : str
        Path to the data file (used to determine report directory).
    report_name : str, optional
        Name of the Markdown report file (default is "tsa_report.md").
    """
    # Determine report directory in root based on data file name
    base_name = os.path.splitext(os.path.basename(data_filepath))[0]
    root_dir = os.path.abspath(os.curdir)
    report_root = os.path.join(root_dir, "reports")
    os.makedirs(report_root, exist_ok=True)

    report_name = f"{base_name}_report.md"
    report_path = os.path.join(report_root, report_name)

    # Save plot to memory
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    # Convert to base 64
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    # MD Embed
    markdown_block = f"""
    ## {title}
    ![{title}](data:image/png;base64,{encoded})
    <sub>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</sub>
    ---
    """

    # Append to report file
    with open(report_path, "a") as f:
        f.write(markdown_block)

def log_plot_to_html_report(fig, title, data_filepath):
    """
    Logs a matplotlib figure to an HTML report file, saving in a directory based on the data file name.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure to be saved.
    title : str
        The title for the plot section in the report.
    data_filepath : str
        Path to the data file (used to determine report directory).
    report_name : str, optional
        Name of the HTML report file (default is "tsa_report.html").
    """
    # Determine report directory in root based on data file name
    base_name = os.path.splitext(os.path.basename(data_filepath))[0]
    root_dir = os.path.abspath(os.curdir)
    report_root = os.path.join(root_dir, "reports")
    os.makedirs(report_root, exist_ok=True)

    report_name = f"{base_name}_report.html"
    report_path = os.path.join(report_root, report_name)

    # Save figure to a BytesIO buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)

    # Convert image to base64 string
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    # HTML content
    html_block = f"""
    <h2>{title}</h2>
    <img src="data:image/png;base64,{encoded}" style="max-width:100%; height:auto;">
    <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    <hr>
    """

    # Write or append to HTML file
    if not os.path.exists(report_path):
        with open(report_path, "w") as f:
            f.write("<html><head><title>Time Series Analysis Report</title></head><body>")
            f.write(html_block)
    else:
        with open(report_path, "a") as f:
            f.write(html_block)

def log_message_to_html_report(message, data_filepath, title="Summary"):
    """
    Logs a text message to an HTML report file, saving in a directory based on the data file name.

    Parameters
    ----------
    message : str
        The message to be logged.
    data_filepath : str
        Path to the data file (used to determine report directory).
    title : str, optional
        The title for the message section (default is "Summary").
    report_name : str, optional
        Name of the HTML report file (default is "tsa_report.html").
    """
    # Determine report directory in root based on data file name
    base_name = os.path.splitext(os.path.basename(data_filepath))[0]
    root_dir = os.path.abspath(os.curdir)
    report_root = os.path.join(root_dir, "reports")
    os.makedirs(report_root, exist_ok=True)
    
    report_name = f"{base_name}_report.html"
    report_path = os.path.join(report_root, report_name)

    html_block = f"""
    <h2>{title}</h2>
    <p style="font-family: monospace; white-space: pre-wrap;">{message}</p>
    <p><em>Logged on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    <hr>
    """

    if not os.path.exists(report_path):
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Time Series Analysis Report</title></head><body>")
            f.write(html_block)
    else:
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(html_block)