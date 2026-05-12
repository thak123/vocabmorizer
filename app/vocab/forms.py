from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

LANGUAGE_CHOICES = [
    ("en", "English"),
    ("hr", "Croatian"),
    ("es", "Spanish"),
    ("pl", "Polish"),
    ("uk", "Ukrainian"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
    ("ar", "Arabic"),
    ("other", "Other"),
]


class VocabularyEntryForm(FlaskForm):
    lecture = StringField("Lecture / Section", validators=[DataRequired(), Length(max=200)])
    date_added = DateField("Date", validators=[DataRequired()])
    word = StringField("Word", validators=[DataRequired(), Length(max=500)])
    # Comma-separated; split on save
    synonyms = StringField("Synonyms", validators=[Optional()], description="Comma-separated")
    antonyms = StringField("Antonyms", validators=[Optional()], description="Comma-separated")
    meaning = TextAreaField("Meaning", validators=[DataRequired()])
    translation_en = StringField(
        "English Translation", validators=[DataRequired(), Length(max=500)]
    )
    metadata_usage = TextAreaField(
        "Morphology / Usage",
        validators=[Optional()],
        description="Morphological notes, example sentences, usage patterns",
    )
    target_language = SelectField("Target Language", choices=LANGUAGE_CHOICES, default="en")
    image = FileField(
        "Image (optional)",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only")],
    )
    submit = SubmitField("Save")
