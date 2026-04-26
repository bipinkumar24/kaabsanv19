# -*- coding: utf-8 -*-
# from odoo import http


# class InheritCar(http.Controller):
#     @http.route('/inherit_car/inherit_car', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inherit_car/inherit_car/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('inherit_car.listing', {
#             'root': '/inherit_car/inherit_car',
#             'objects': http.request.env['inherit_car.inherit_car'].search([]),
#         })

#     @http.route('/inherit_car/inherit_car/objects/<model("inherit_car.inherit_car"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inherit_car.object', {
#             'object': obj
#         })
