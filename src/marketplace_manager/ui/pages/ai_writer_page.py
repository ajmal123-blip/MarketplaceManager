"""Editable local AI listing generator UI."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from marketplace_manager.ai.models import ListingRequest, ListingResult, validate_listing_request
from marketplace_manager.ai.providers import AIProvider, AIServiceUnavailableError, get_provider
from marketplace_manager.database.listing_repository import ListingDraft, ListingDraftRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.ui.pages.common import page_header


class AIWriterPage(QWidget):
    """Generate, edit, copy, and save local listing drafts without publishing."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        super().__init__()
        self._provider = provider
        self._connection = initialize_database()
        self._draft_repository = ListingDraftRepository(self._connection)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(14)
        page_header(layout, "AI Writer", "Generate editable listing drafts. Nothing is published automatically.")

        form = QFormLayout()
        self.product_title = QLineEdit()
        self.product_title.setPlaceholderText("e.g. Vintage desk lamp")
        self.category = QLineEdit()
        self.condition = QLineEdit()
        self.price = QLineEdit()
        self.price.setPlaceholderText("e.g. 24.99")
        self.location = QLineEdit()
        self.details = QTextEdit()
        self.details.setPlaceholderText("Materials, features, dimensions, included accessories, and other useful details")
        self.details.setFixedHeight(75)
        for label, widget in (
            ("Product title *", self.product_title),
            ("Category *", self.category),
            ("Condition *", self.condition),
            ("Price *", self.price),
            ("Location *", self.location),
            ("Product details *", self.details),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.generate_button = QPushButton("Generate Listing")
        self.clear_button = QPushButton("Clear")
        actions.addWidget(self.generate_button)
        actions.addWidget(self.clear_button)
        actions.addStretch()
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(120)
        actions.addWidget(self.progress)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("placeholderText")
        actions.addWidget(self.status_label)
        layout.addLayout(actions)

        output_layout = QFormLayout()
        self.generated_title = QLineEdit()
        self.generated_description = QTextEdit()
        self.generated_description.setFixedHeight(90)
        self.short_description = QTextEdit()
        self.short_description.setFixedHeight(65)
        self.keywords = QLineEdit()
        output_layout.addRow("Listing title", self._with_copy(self.generated_title))
        output_layout.addRow("Listing description", self._with_copy(self.generated_description))
        output_layout.addRow("Short description", self._with_copy(self.short_description))
        output_layout.addRow("Keywords", self._with_copy(self.keywords))
        layout.addLayout(output_layout)

        self.save_button = QPushButton("Save Listing")
        self.save_button.clicked.connect(self.save_draft)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()

        self.generate_button.clicked.connect(self.generate)
        self.clear_button.clicked.connect(self.clear)

    @staticmethod
    def _with_copy(widget: QWidget) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        copy_button = QPushButton("Copy")
        copy_button.setFixedWidth(64)
        copy_button.clicked.connect(lambda: AIWriterPage._copy_widget_value(widget))
        row.addWidget(widget, 1)
        row.addWidget(copy_button)
        return container

    @staticmethod
    def _copy_widget_value(widget: QWidget) -> None:
        if isinstance(widget, QTextEdit):
            value = widget.toPlainText()
        else:
            value = widget.text()  # type: ignore[attr-defined]
        QApplication.clipboard().setText(value)

    def _request(self) -> ListingRequest:
        return ListingRequest(
            self.product_title.text().strip(), self.category.text().strip(), self.condition.text().strip(),
            self.price.text().strip(), self.location.text().strip(), self.details.toPlainText().strip(),
        )

    def generate(self) -> bool:
        request = self._request()
        errors = validate_listing_request(request)
        if errors:
            message = "Please correct the following:\n" + "\n".join(f"• {error}" for error in errors)
            self.status_label.setText("Input needs attention")
            QMessageBox.warning(self, "Check listing details", message)
            return False

        self._set_loading(True)
        try:
            provider = self._provider or get_provider()
            result = provider.generate_listing(request)
            self._set_result(result)
            self.status_label.setText("Listing generated")
            return True
        except AIServiceUnavailableError as error:
            self.status_label.setText("Provider unavailable")
            QMessageBox.information(self, "AI unavailable", str(error))
        except Exception:
            self.status_label.setText("Generation failed")
            QMessageBox.critical(self, "AI error", "The listing could not be generated. Please try again later.")
        finally:
            self._set_loading(False)
        return False

    def _set_result(self, result: ListingResult) -> None:
        self.generated_title.setText(result.title)
        self.generated_description.setPlainText(result.description)
        self.short_description.setPlainText(result.short_description)
        self.keywords.setText(result.keywords)

    def _set_loading(self, loading: bool) -> None:
        self.generate_button.setEnabled(not loading)
        self.clear_button.setEnabled(not loading)
        self.save_button.setEnabled(not loading)
        self.progress.setRange(0, 0 if loading else 1)
        if not loading:
            self.progress.setValue(0)
        QApplication.processEvents()

    def save_draft(self) -> bool:
        values = (
            self.generated_title.text().strip(), self.generated_description.toPlainText().strip(),
            self.short_description.toPlainText().strip(), self.keywords.text().strip(),
        )
        if not values[0]:
            self.status_label.setText("Nothing to save")
            QMessageBox.warning(self, "Nothing to save", "Generate or enter a listing title first.")
            return False
        try:
            self._draft_repository.create(ListingDraft(None, *values))
            self.status_label.setText("Listing saved locally")
            QMessageBox.information(self, "Listing saved", "The listing draft was saved locally. It was not published anywhere.")
            return True
        except Exception:
            self.status_label.setText("Save failed")
            QMessageBox.critical(self, "Save error", "The local listing draft could not be saved.")
            return False

    def clear(self) -> None:
        for widget in (self.product_title, self.category, self.condition, self.price, self.location,
                       self.generated_title, self.keywords):
            widget.clear()
        self.details.clear()
        self.generated_description.clear()
        self.short_description.clear()
        self.status_label.setText("Ready")
