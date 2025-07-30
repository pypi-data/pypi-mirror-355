# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Employee + Stock Integration",
    "version": "14.0.1.3.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "auto_install": True,
    "depends": [
        "ssi_hr_employee",
        "ssi_stock",
    ],
    "data": [
        "data/location_type_data.xml",
        "views/hr_employee_views.xml",
    ],
    "demo": [],
}
