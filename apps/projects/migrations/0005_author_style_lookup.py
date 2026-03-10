import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_outlinenode_content"),
        ("projects", "0004_contenttype_planning_fields"),
        ("projects", "0004_author_style_lookup"),
    ]

    operations = []
