# -*- coding: utf-8 -*-
# from odoo import http


# class ExtendContract(http.Controller):
#     @http.route('/extend_contract/extend_contract', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/extend_contract/extend_contract/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('extend_contract.listing', {
#             'root': '/extend_contract/extend_contract',
#             'objects': http.request.env['extend_contract.extend_contract'].search([]),
#         })

#     @http.route('/extend_contract/extend_contract/objects/<model("extend_contract.extend_contract"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('extend_contract.object', {
#             'object': obj
#         })
