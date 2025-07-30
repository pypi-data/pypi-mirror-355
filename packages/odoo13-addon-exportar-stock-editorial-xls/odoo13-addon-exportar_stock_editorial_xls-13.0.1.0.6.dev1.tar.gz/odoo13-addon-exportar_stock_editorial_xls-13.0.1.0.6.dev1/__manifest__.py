# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#    This version is modify by Team Devcontrol for using for radikal editorials
#
#############################################################################

{
    'name': 'Export Stock Editorial',
    'version': '13.0.1.0.5',
    'summary': 'Muestra el stock actual de productos en la editorial.',
    'description': 'Muestra el stock actual de productos, utilizado para el conjunto de módulos de Gestión editorial.',  
    'category': 'Warehouse',
    'author': 'Colectivo DEVCONTROL',
    'author_email': 'devcontrol@sindominio.net',
    'maintainer': 'Colectivo DEVCONTROL',
    'company': 'Colectivo DEVCONTROL',
    'website': 'https://framagit.org/devcontrol',
    'depends': [
                'base',
                'stock',
                'sale',
                'purchase',
                'gestion_editorial',
                ],
    'data': [
            'views/wizard_view.xml',
            'views/action_manager.xml',
            ],
    'demo': [],
    'test': [],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'auto_install': False,
    'license': 'AGPL-3',
}