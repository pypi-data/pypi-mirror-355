import customtkinter as ctk
from .cagr import calculate_cagr


class CAGRCalculatorGUI:
    start_value = None
    end_value = None
    years = None

    def __init__(self, root):
        self.root = root
        self.root.title("Sigmavest CAGR Calculator")
        self.root.geometry("500x400")

        # Configure appearance
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Title
        title_label = ctk.CTkLabel(self.main_frame, text="CAGR Calculator", font=("Arial", 24, "bold"))
        title_label.pack(pady=10)

        # Input frame
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(pady=10, padx=10, fill="x")

        # Starting Value
        ctk.CTkLabel(input_frame, text="Starting Value ($):").pack(pady=(10, 0))
        self.start_value = ctk.CTkEntry(input_frame)
        self.start_value.pack(pady=5, padx=10, fill="x")

        # Ending Value
        ctk.CTkLabel(input_frame, text="Ending Value ($):").pack(pady=(10, 0))
        self.end_value = ctk.CTkEntry(input_frame)
        self.end_value.pack(pady=5, padx=10, fill="x")

        # Years
        ctk.CTkLabel(input_frame, text="Time Period (years):").pack(pady=(10, 0))
        self.years = ctk.CTkEntry(input_frame)
        self.years.pack(pady=5, padx=10, fill="x")

        # Calculate Button
        calculate_btn = ctk.CTkButton(self.main_frame, text="Calculate CAGR", command=self.calculate)
        calculate_btn.pack(pady=20)

        # Result frame
        self.result_frame = ctk.CTkFrame(self.main_frame)
        self.result_frame.pack(pady=10, padx=10, fill="x")

        self.result_label = ctk.CTkLabel(self.result_frame, text="CAGR: ", font=("Arial", 16, "bold"))
        self.result_label.pack(pady=20)

    def calculate(self):
        try:
            start = float(self.start_value.get())
            end = float(self.end_value.get())
            years = float(self.years.get())

            cagr = calculate_cagr(start, end, years)
            self.result_label.configure(
                text=f"CAGR: {cagr:.2%}",
                text_color="#2ECC71",  # Green color for positive result
            )
        except ValueError as e:
            self.result_label.configure(
                text=f"Error: {str(e)}",
                text_color="#E74C3C",  # Red color for error
            )


def run_gui(): # pragma no cover
    root = ctk.CTk()
    CAGRCalculatorGUI(root)
    root.mainloop()
