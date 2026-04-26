# -*- coding: utf-8 -*-
# from odoo import http


# class ExtendAsset(http.Controller):
#     @http.route('/extend_asset/extend_asset', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/extend_asset/extend_asset/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('extend_asset.listing', {
#             'root': '/extend_asset/extend_asset',
#             'objects': http.request.env['extend_asset.extend_asset'].search([]),
#         })

#     @http.route('/extend_asset/extend_asset/objects/<model("extend_asset.extend_asset"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('extend_asset.object', {
#             'object': obj
#         })
