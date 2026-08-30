"""PDF and Excel report generation entrypoints."""
from app.services.report_pdf import generate_pdf_report
from app.services.report_xlsx import generate_xlsx_report

__all__ = ["generate_pdf_report", "generate_xlsx_report"]
