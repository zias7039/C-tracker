# main.py - Enhanced Error Handling
import sys
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("debug_log.txt", mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)


def exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler to capture unhandled exceptions"""
    logging.critical("Unhandled exception:",
                     exc_info=(exc_type, exc_value, exc_traceback))
    error_msg = f"{exc_type.__name__}: {exc_value}"

    # Display error dialog if possible
    try:
        if QApplication.instance():
            QMessageBox.critical(None, "Critical Error",
                                 f"Application encountered a critical error:\n{error_msg}")
    except:
        pass  # Can't show dialog, already logged to file


# Install global exception handler
sys.excepthook = exception_handler

if __name__ == "__main__":
    app = None
    try:
        logging.info("Starting application initialization")

        # Initialize QApplication with diagnostic output
        logging.debug("Creating QApplication instance")
        app = QApplication(sys.argv)
        logging.debug("QApplication created successfully")

        # Import modules with explicit error handling
        logging.debug("Importing overlay module")
        try:
            from overlay import Overlay

            logging.debug("Overlay module imported successfully")
        except ImportError as e:
            logging.critical(f"Failed to import Overlay: {e}")
            QMessageBox.critical(None, "Import Error",
                                 f"Failed to load required component:\n{str(e)}")
            sys.exit(1)

        # Create overlay with protection against initialization errors
        logging.debug("Creating Overlay instance")
        try:
            overlay = Overlay()
            logging.debug("Overlay instance created successfully")
        except Exception as e:
            logging.critical(f"Overlay initialization failed: {e}",
                             exc_info=True)
            QMessageBox.critical(None, "Initialization Error",
                                 f"Failed to initialize application:\n{str(e)}")
            sys.exit(1)

        # Show overlay with protection
        logging.debug("Showing overlay window")
        try:
            overlay.show()
            logging.info("Application initialized successfully")
        except Exception as e:
            logging.critical(f"Failed to show overlay: {e}",
                             exc_info=True)
            QMessageBox.critical(None, "Display Error",
                                 f"Failed to display application window:\n{str(e)}")
            sys.exit(1)

        # Enter application main loop
        sys.exit(app.exec_())

    except Exception as e:
        logging.critical(f"Critical error during application startup: {e}",
                         exc_info=True)
        if app:
            QMessageBox.critical(None, "Startup Error",
                                 f"Application startup failed:\n{str(e)}")
        sys.exit(1)
