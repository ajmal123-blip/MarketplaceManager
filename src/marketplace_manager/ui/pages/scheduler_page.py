"""UI for local internal-task scheduling."""
from datetime import datetime
from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from marketplace_manager.database.service import initialize_database
from marketplace_manager.scheduler.service import SchedulerService, TASK_TYPES
from marketplace_manager.ui.pages.common import page_header

class SchedulerPage(QWidget):
    def __init__(self):
        super().__init__(); self.service=SchedulerService(initialize_database()); layout=QVBoxLayout(self); layout.setContentsMargins(36,32,36,32); page_header(layout,"Scheduler","Schedule internal application tasks. Nothing is published automatically.")
        controls=QHBoxLayout(); add=QPushButton("Create task"); toggle=QPushButton("Enable / Disable"); run=QPushButton("Run due tasks"); delete=QPushButton("Delete"); history=QPushButton("History")
        for button in (add,toggle,run,delete,history): controls.addWidget(button)
        controls.addStretch(); layout.addLayout(controls); self.table=QTableWidget(0,5); self.table.setHorizontalHeaderLabels(["Type","Scheduled for","Enabled","Status","ID"]); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.hideColumn(4); layout.addWidget(self.table,1)
        add.clicked.connect(self.create); toggle.clicked.connect(self.toggle); run.clicked.connect(self.run_due); delete.clicked.connect(self.delete); history.clicked.connect(self.show_history); self.refresh()
    def refresh(self):
        rows=self.service.list_tasks(); self.table.setRowCount(len(rows))
        for index,row in enumerate(rows):
            for col,value in enumerate((row["task_type"],row["scheduled_at"],"Yes" if row["enabled"] else "No",row["status"],str(row["id"]))): self.table.setItem(index,col,QTableWidgetItem(value))
    def selected_id(self):
        row=self.table.currentRow(); return int(self.table.item(row,4).text()) if row>=0 else None
    def create(self):
        dialog=QDialog(self); dialog.setWindowTitle("Create scheduled task"); form=QFormLayout(dialog); kind=QComboBox(); kind.addItems(TASK_TYPES); when=QDateTimeEdit(QDateTime.currentDateTime()); when.setCalendarPopup(True); form.addRow("Internal task",kind); form.addRow("Date and time",when); buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec(): self.service.create(kind.currentText(),when.dateTime().toPython()); self.service.connection.commit(); self.refresh()
    def toggle(self):
        task_id=self.selected_id()
        if task_id is None: return
        row=next(row for row in self.service.list_tasks() if row["id"]==task_id); self.service.set_enabled(task_id,not bool(row["enabled"])); self.refresh()
    def run_due(self): self.service.run_due(); self.refresh(); QMessageBox.information(self,"Scheduler","Due internal tasks were processed.")
    def delete(self):
        task_id=self.selected_id()
        if task_id is not None and QMessageBox.question(self,"Delete task","Delete the selected scheduled task?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes: self.service.delete(task_id); self.refresh()
    def show_history(self):
        task_id=self.selected_id()
        if task_id is None: return
        entries=self.service.history(task_id); text="\n".join(f"{row['executed_at']} — {row['status']}: {row['message']}" for row in entries) or "No executions yet."
        QMessageBox.information(self,"Execution history",text)
