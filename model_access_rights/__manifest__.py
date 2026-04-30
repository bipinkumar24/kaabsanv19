# -*- coding: utf-8 -*-

{
    "name": "Model Access Rights",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Hide create, edit, delete, export, and archive actions per model and group.",
    "description": """
        Configure model-specific UI action restrictions by user group, including
        create/update, delete, export, and archive or unarchive options.
    """,
    "author": "Bipin Prajapati",
    "depends": [
        "base_setup",
        "mail",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/model_access_rights_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "model_access_rights/static/src/js/form_controller.js",
            "model_access_rights/static/src/js/list_controller.js",
        ]
    },
    "images": ["static/description/banner.png"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
