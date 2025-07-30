import sys
import traceback

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich import box

from .errors import Error
from .utils import load_path


class TraceEase:
    __version__ = "0.1.0"

    def __init__(self, file_location=True, traceback_summary=True, explanation=True, advanced_traceback=False, theme='default', catch_unhandled=True):
        self.console = Console()
        self.themes = load_path('themes.json')
        self.theme = self.themes.get(theme, self.themes['default'])
        self.file_loc = file_location
        self.tb_summary = traceback_summary
        self.explanation = explanation
        self.advanced_tb = advanced_traceback
        if catch_unhandled:
            self.enable_global_handler()

    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        if exc_type in (KeyboardInterrupt, SystemExit):
            return  # Allow default behavior

        # Extract last traceback frame (the one where error occurred)
        tb_frames = traceback.extract_tb(exc_traceback)
        if tb_frames:
            last_frame = tb_frames[-1]
            filename = last_frame.filename
            lineno = last_frame.lineno
            code_line = last_frame.line
        else:
            filename = lineno = code_line = "Unknown"

        # Format full traceback
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        clean_trace = self.format_trace(tb_str)
        explanation = self.explain_error(exc_value)

        # Print top banner
        self.console.rule(f"[bold {self.theme['rule_color']}]{self.theme['icons']['error']} TraceEase Error Detected[/bold {self.theme['rule_color']}]")

        if self.file_loc:
            # Location and error
            self.console.print(
                Panel.fit(
                    f"[bold]{self.theme['icons']['file']} File:[/bold] [{self.theme['file_color']}]{filename}[/{self.theme['file_color']}]",
                    title="Take Me to The Error",
                    border_style=self.theme['rule_color'],
                    box=box.ROUNDED
                )
            )

        if self.tb_summary:
            # Display last few lines of traceback
            self.console.print(
                Panel(
                    clean_trace,
                    title=f"{self.theme['icons']['trace']} Traceback Summary",
                    border_style=self.theme['trace_color'],
                    box=box.ROUNDED,
                    expand=False
                )
            )
        
        if self.explanation:
            # Display explanation / suggestion
            self.console.print(
                Panel(
                    f"{self.theme['icons']['hint']} {explanation}",
                    title="What This Means",
                    border_style=self.theme['explanation_color'],
                    box=box.ROUNDED,
                    expand=False
                )
            )

        if self.advanced_tb:
            self.console.print()
            self.console.print(f"[bold {self.theme['full_tb_color']}]{self.theme['icons']['advanced']} Full Traceback (for advanced users):[/bold {self.theme['full_tb_color']}]")
            self.console.print(Panel(
                tb_str.strip(),
                title="🔎 Full Traceback",
                border_style="dim",
                style="dim",
                box=box.ROUNDED,
                expand=False
            ))

        # Final rule
        self.console.rule(f"[bold {self.theme['rule_color']}]End of TraceEase Report[/bold {self.theme['rule_color']}]")

    def enable_global_handler(self):
        sys.excepthook = self.global_exception_handler

    #enabling and disabling sections
    def enable_file_location(self):
        self.file_loc = True
    
    def disable_file_location(self):
        self.file_loc = False
    
    def enable_traceback_summary(self):
        self.tb_summary = True
    
    def disable_traceback_summary(self):
        self.tb_summary = False
    
    def enable_explanation(self):
        self.explanation = True
    
    def disable_explanation(self):
        self.explanation = False
    
    def enable_advanced_traceback(self):
        self.advanced_tb = True
    
    def disable_advanced_traceback(self):
        self.advanced_tb = False


    def format_trace(self, tb_str: str) -> str:
        lines = tb_str.strip().split('\n')
        relevant = lines[-3:]  # Adjust based on verbosity preference
        return '\n'.join(f"[blue]➡️[/blue] {line}" for line in relevant)

    def explain_error(self, e: Exception) -> str:
        error_type = type(e).__name__
        return str(Error(error_type))