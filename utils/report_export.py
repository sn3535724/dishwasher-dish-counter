from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_FOLDER = PROJECT_ROOT / "static" / "reports"
REPORTS_FOLDER.mkdir(parents=True, exist_ok=True)


def export_history_to_excel(records: list[dict]) -> str:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "История"

    headers = [
        "ID", "Дата и время", "Исходный файл", "Всего предметов",
        "Состав", "Средняя уверенность, %", "Время, сек.",
        "Режим", "Размер, px", "Порог, %",
    ]
    worksheet.append(headers)

    for record in records:
        details = ", ".join(
            f"{name}: {count}" for name, count in record["class_counts"].items()
        ) or "объекты не найдены"

        worksheet.append([
            record["id"], record["timestamp"], record["original_filename"],
            record["dish_count"], details, record["average_confidence"],
            record["processing_time"], record["mode"], record["image_size"],
            record["confidence"],
        ])

    fill = PatternFill("solid", fgColor="2F5597")
    font = Font(color="FFFFFF", bold=True)
    for cell in worksheet[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")

    for column_cells in worksheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        letter = get_column_letter(column_cells[0].column)
        worksheet.column_dimensions[letter].width = min(max_length + 3, 45)

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_FOLDER / f"dish_counter_report_{timestamp}.xlsx"
    workbook.save(report_path)
    return str(report_path)
