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
#############################################################################
from datetime import datetime
import pytz
import json
import datetime
import io
from odoo import fields, models, _
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class StockReport(models.TransientModel):
    _name = "wizard.stock.history"
    _description = "Current Stock History"

    warehouse = fields.Many2many(
        "stock.warehouse", "wh_wiz_rel", "wh", "wiz", string="Warehouse", required=True
    )
    category = fields.Many2many(
        "product.category", "categ_wiz_rel", "categ", "wiz", string="Warehouse"
    )

    def export_xls(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "warehouse": self.warehouse.ids,
            "category": self.category.ids,
        }
        return {
            "type": "ir_actions_xlsx_download",
            "data": {
                "model": "wizard.stock.history",
                "options": json.dumps(data, default=date_utils.json_default),
                "output_format": "xlsx",
                "report_name": "Current Stock History",
            },
        }

    def get_warehouse(self, data):
        wh = data.warehouse.mapped("id")
        obj = self.env["stock.warehouse"].search([("id", "in", wh)])
        l1 = []
        l2 = []
        for j in obj:
            l1.append(j.name)
            l2.append(j.id)
        return l1, l2

    def get_lines(self, data, warehouse):
        lines = []
        categ_id = data.mapped("id")
        if categ_id:
            categ_products = self.env["product.product"].search(
                [("categ_id", "in", categ_id)]
            )
        else:
            categ_products = self.env["product.product"].search([])

        for obj in categ_products:
            authors = ', '.join([author.name for author in obj.author_name]) if obj.author_name else ''
            liquidated_sales_qty = obj.get_liquidated_sales_qty()
            liquidated_purchases_qty = obj.get_liquidated_purchases_qty()
            received_qty = obj.get_received_qty()
            purchase_deposit_qty = received_qty - liquidated_purchases_qty

            # Calcula el total de productos "En almacén" (= on hand)
            on_hand_qty = obj.get_product_quantity_in_location(
                self.env.ref("stock.stock_location_stock")
            )

            # Calcula el total de productos "En distribución - En librerias"
            in_distribution_qty = obj.get_product_quantity_in_location(
                self.env.company.location_venta_deposito_id
            )

            # Suma de libros en Partner Location/Autores e hijas 
            # + Libros vendidos con tarifa "Venta a Autoras"
            books_delivered_authorship = obj.get_product_quantity_in_location(
                self.env.ref("gestion_editorial.stock_location_authors")
            ) + obj.get_sales_to_author_qty()

            books_for_promotion = obj.get_product_quantity_in_location(
                self.env.company.location_promotion_id
            )

            destroyed = 0
            for scrap_location in self.env["stock.location"].search([("scrap_location", "=", True)]):
                destroyed += obj.get_product_quantity_in_location(scrap_location)

            vals = {
                "sku": obj.default_code,
                "name": obj.name,
                "authors": authors,
                "category": obj.categ_id.name,
                "list_price": obj.list_price,
                "owned": on_hand_qty + in_distribution_qty,
                "available": on_hand_qty,
                "in_distribution": in_distribution_qty,
                "purchase_deposit_qty": purchase_deposit_qty,
                "received_qty": received_qty,
                "liquidated_purchases_qty": liquidated_purchases_qty,
                "liquidated_sales_qty": liquidated_sales_qty,
                "books_delivered_authorship": books_delivered_authorship,
                "books_for_promotion": books_for_promotion,
                "destroyed": destroyed,
            }
            lines.append(vals)
        return lines

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        lines = self.browse(data["ids"])
        d = lines.category
        get_warehouse = self.get_warehouse(lines)
        count = len(get_warehouse[0]) * 11 + 12
        comp = self.env.user.company_id.name
        sheet = workbook.add_worksheet("Stock Info")
        format0 = workbook.add_format(
            {"font_size": 20, "align": "center", "bold": True}
        )
        format1 = workbook.add_format(
            {"font_size": 14, "align": "vcenter", "bold": True}
        )
        format11 = workbook.add_format(
            {"font_size": 12, "align": "center", "bold": True}
        )
        format21 = workbook.add_format(
            {"font_size": 10, "align": "center", "bold": True}
        )
        format3 = workbook.add_format({"bottom": True, "top": True, "font_size": 12})
        format4 = workbook.add_format({"font_size": 12, "align": "left", "bold": True})
        font_size_8 = workbook.add_format({"font_size": 8, "align": "center"})
        font_size_8_l = workbook.add_format({"font_size": 8, "align": "left"})
        red_mark = workbook.add_format({"font_size": 8, "bg_color": "red"})
        justify = workbook.add_format({"font_size": 12})
        format3.set_align("center")
        justify.set_align("justify")
        format1.set_align("center")
        red_mark.set_align("center")
        sheet.merge_range(1, 7, 2, 10, "Product Stock Info", format0)
        sheet.merge_range(3, 7, 3, 10, comp, format11)
        w_house = ", "
        cat = ", "
        c = []
        d1 = d.mapped("id")
        if d1:
            for i in d1:
                c.append(self.env["product.category"].browse(i).name)
            cat = cat.join(c)
            sheet.merge_range(4, 0, 4, 1, "Category(s) : ", format4)
            sheet.merge_range(4, 2, 4, 3 + len(d1), cat, format4)
        sheet.merge_range(5, 0, 5, 1, "Almacenes : ", format4)
        w_house = w_house.join(get_warehouse[0])
        sheet.merge_range(5, 2, 5, 3 + len(get_warehouse[0]), w_house, format4)
        user = self.env["res.users"].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else "UTC")
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        sheet.merge_range(
            "A8:G8", "Fecha: " + str(times.strftime("%Y-%m-%d %H:%M %p")), format1
        )
        sheet.merge_range(7, 7, 7, count, "Almacenes", format1)
        sheet.merge_range("A9:G9", "Información de producto", format11)
        w_col_no = 9
        w_col_no1 = 10
        for i in get_warehouse[0]:
            w_col_no = w_col_no + 11
            sheet.merge_range(8, w_col_no1, 8, w_col_no, i, format11)
            w_col_no1 = w_col_no1 + 11
        sheet.write(9, 0, "SKU", format21)
        sheet.write(9, 1, "Nombre", format21)
        sheet.write(9, 2, "Autores", format21)
        sheet.write(9, 3, "Categoría", format21)
        sheet.write(9, 4, "PVP", format21)
        sheet.set_column("B:B", 35)
        sheet.set_column("C:C", 23)
        sheet.set_column("E:K", 17)
        sheet.set_column("L:L", 22)
        sheet.set_column("M:M", 21)
        sheet.set_column("N:N", 17)

        p_col_no1 = 5

        for i in get_warehouse[0]:
            sheet.write(9, p_col_no1, "Existencias totales", format21)
            sheet.write(9, p_col_no1 + 1, "En almacén", format21)
            sheet.write(9, p_col_no1 + 2, "En distribución", format21)
            sheet.write(9, p_col_no1 + 3, "Depósito de compra", format21)
            sheet.write(9, p_col_no1 + 4, "Recibidos", format21)
            sheet.write(9, p_col_no1 + 5, "Compras liquidadas", format21)
            sheet.write(9, p_col_no1 + 6, "Ventas liquidadas", format21)
            sheet.write(9, p_col_no1 + 7, "Entregados a autoría", format21)
            sheet.write(9, p_col_no1 + 8, "Promoción", format21)
            sheet.write(9, p_col_no1 + 9, "Destruidos", format21)
            p_col_no1 = p_col_no1 + 10
        prod_row = 10
        prod_col = 0
        for i in get_warehouse[1]:
            get_line = self.get_lines(d, i)
            for each in get_line:
                sheet.write(prod_row, prod_col, each["sku"], font_size_8)
                sheet.write(prod_row, prod_col + 1, each["name"], font_size_8_l)
                sheet.write(prod_row, prod_col + 2, each["authors"], font_size_8_l) 
                sheet.write(prod_row, prod_col + 3, each["category"], font_size_8_l)
                sheet.write(prod_row, prod_col + 4, each["list_price"], font_size_8)
                prod_row = prod_row + 1
            break
        prod_row = 10
        prod_col = 5
        for i in get_warehouse[1]:
            get_line = self.get_lines(d, i)
            for each in get_line:
                cell_format = red_mark if each["owned"] < 0 else font_size_8
                sheet.write(prod_row, prod_col, each["owned"], cell_format)

                cell_format = red_mark if each["available"] < 0 else font_size_8
                sheet.write(prod_row, prod_col + 1, each["available"], cell_format)

                cell_format = red_mark if each["in_distribution"] < 0 else font_size_8
                sheet.write(
                    prod_row, prod_col + 2, each["in_distribution"], cell_format
                )

                cell_format = (
                    red_mark if each["purchase_deposit_qty"] < 0 else font_size_8
                )
                sheet.write(
                    prod_row, prod_col + 3, each["purchase_deposit_qty"], cell_format
                )

                cell_format = red_mark if each["received_qty"] < 0 else font_size_8
                sheet.write(prod_row, prod_col + 4, each["received_qty"], cell_format)

                cell_format = (
                    red_mark if each["liquidated_purchases_qty"] < 0 else font_size_8
                )
                sheet.write(
                    prod_row,
                    prod_col + 5,
                    each["liquidated_purchases_qty"],
                    cell_format,
                )

                cell_format = (
                    red_mark if each["liquidated_sales_qty"] < 0 else font_size_8
                )
                sheet.write(
                    prod_row, prod_col + 6, each["liquidated_sales_qty"], cell_format
                )

                sheet.write(prod_row, prod_col + 7, each["books_delivered_authorship"], font_size_8)
                sheet.write(prod_row, prod_col + 8, each["books_for_promotion"], font_size_8)
                sheet.write(prod_row, prod_col + 9, each["destroyed"], font_size_8)

                prod_row = prod_row + 1

            prod_row = 10
            prod_col = prod_col + 14
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
