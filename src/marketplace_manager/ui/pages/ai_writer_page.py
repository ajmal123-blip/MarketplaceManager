"""Editable local AI listing generator UI."""
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget
from marketplace_manager.ai.models import ListingRequest
from marketplace_manager.ai.providers import AIServiceUnavailableError, get_provider
from marketplace_manager.database.service import initialize_database
from marketplace_manager.ui.pages.common import page_header

class AIWriterPage(QWidget):
    def __init__(self):
        super().__init__(); layout=QVBoxLayout(self); layout.setContentsMargins(36,32,36,32); page_header(layout,"AI Writer","Generate editable listing drafts. Nothing is published automatically.")
        form=QFormLayout(); self.product_title=QLineEdit(); self.category=QLineEdit(); self.condition=QLineEdit(); self.price=QLineEdit(); self.location=QLineEdit(); self.details=QTextEdit(); self.details.setFixedHeight(75)
        for label,widget in (("Product title",self.product_title),("Category",self.category),("Condition",self.condition),("Price",self.price),("Location",self.location),("Product details",self.details)): form.addRow(label,widget)
        layout.addLayout(form); generate=QPushButton("Generate draft"); generate.clicked.connect(self.generate); layout.addWidget(generate)
        output=QFormLayout(); self.generated_title=QLineEdit(); self.generated_description=QTextEdit(); self.short_description=QTextEdit(); self.keywords=QLineEdit()
        for label,widget in (("Listing title",self.generated_title),("Listing description",self.generated_description),("Short description",self.short_description),("Keywords",self.keywords)): output.addRow(label,widget)
        layout.addLayout(output); save=QPushButton("Save local draft"); save.clicked.connect(self.save_draft); layout.addWidget(save); layout.addStretch()
    def generate(self):
        if not self.product_title.text().strip(): QMessageBox.warning(self,"Product title required","Enter a product title before generating a draft."); return
        request=ListingRequest(self.product_title.text().strip(),self.category.text().strip(),self.condition.text().strip(),self.price.text().strip(),self.location.text().strip(),self.details.toPlainText().strip())
        try: result=get_provider().generate_listing(request)
        except AIServiceUnavailableError as error: QMessageBox.information(self,"AI unavailable",str(error)); return
        except Exception: QMessageBox.critical(self,"AI error","The AI service could not generate a draft. Please try again later."); return
        self.generated_title.setText(result.title); self.generated_description.setPlainText(result.description); self.short_description.setPlainText(result.short_description); self.keywords.setText(result.keywords)
    def save_draft(self):
        if not self.generated_title.text().strip(): QMessageBox.warning(self,"Nothing to save","Generate or enter a listing title first."); return
        try:
            connection=initialize_database(); connection.execute("INSERT INTO listing_drafts (title, description, short_description, keywords) VALUES (?, ?, ?, ?)",(self.generated_title.text().strip(),self.generated_description.toPlainText().strip(),self.short_description.toPlainText().strip(),self.keywords.text().strip())); connection.commit(); connection.close()
            QMessageBox.information(self,"Draft saved","Your edited listing draft was saved locally. It was not published anywhere.")
        except Exception: QMessageBox.critical(self,"Save error","The local draft could not be saved.")
