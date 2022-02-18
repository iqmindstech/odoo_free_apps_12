from werkzeug.utils import redirect

from odoo import http
from odoo.http import request
from odoo import api,models
from odoo.addons.website_sale.controllers.main import WebsiteSale
import datetime


class WebsiteSaleInherit(WebsiteSale):

	@http.route(['/shop/confirmation'], type='http', auth="public", website=True, csrf=False)
	def payment_confirmation(self, **post):
		print('\n\n\n <<<<<<<<<<< In payment_confirmation method of website_sale module [ CHILD ] >>>>>>>>>>\n\n\n')
		print('\npost 5645\n',post,'\n\n', request.session)
		sale_obj=request.env['sale.order']
		invoice_obj=request.env['account.invoice']
		payment_obj=request.env['account.payment']
		if post:
			print("111111111111111111111111111111")
			if post.get('RESPONSE_CODE') =='300' and post.get('STATUS') == 'Invalid' :
				print("post.get('RESPONSE_CODE') ==300")
				data = {'response_message' : post.get('STATUS')}
				return request.render('payment_paycaps.paycaps_msg', data)

			elif post.get('RESPONSE_CODE') == '010' and post.get('STATUS') == 'Cancelled':
				data = {'response_message' : post.get('RESPONSE_MESSAGE')}
				return request.render('payment_paycaps.paycaps_msg', data)
			else:
				print("Sucess Paycaps")
				obj = http.request.env['account.journal'].sudo().search([('type', '=', 'bank')])
				for i in obj:
					if i.name == 'Bank':
						payment_type = i.id
				if post.get('RESPONSE_CODE') == '000' and post.get('RESPONSE_MESSAGE'):
					if post['RESPONSE_MESSAGE'] == 'SUCCESS':

					    reference = post['ORDER_ID']
					    sale_order_id =sale_obj.sudo().search([('name', '=', reference)])
					    order = sale_obj.sudo().search([('id', '=', sale_order_id.id)])
					    if not order:
					        print("^^^^^^^^^^^^^",order)
					        invoice_val = invoice_obj.sudo().search([('number', '=', reference)])
					        invoice_id = invoice_obj.sudo().search([('id', '=', invoice_val.id)])
					        if invoice_id:

					        	payment_id = payment_obj.sudo().search(
								[('invoice_ids', 'in', invoice_id.id)], limit=1)
						        print("payment_idpayment_idpayment_id",payment_id)
						        if not payment_id:
						        	journal_id = request.env['account.journal'].sudo().search([('name', '=', 'Bank')], limit=1)
						        	method_id = request.env['account.payment.method'].sudo().search([('code', '=', 'manual')], limit=1)
						        	payment_id = payment_obj.sudo().create({
											    'payment_type': 'inbound',
											    'partner_type': 'customer',
											    'partner_id': invoice_id.partner_id.id,
											    'payment_date': invoice_id.date_invoice,
											    'communication': 'Paid By Paycaps',
											   
											    'journal_id': journal_id.id,
											    'currency_id': invoice_id.currency_id.id,
											    'payment_method_id': method_id.id,
											    'amount': invoice_id.amount_total,
											    })
					        	if payment_id:
					        		payment_transaction_id = request.env['payment.transaction'].sudo().search(
									[('invoice_ids', 'in', invoice_id.id)],
									limit=1)
					        		if payment_transaction_id:
					        			payment_transaction_id.payment_id = payment_id.id
					        			payment_transaction_id.state = 'done'
									# payment_transaction_id.acquirer_reference=post['ACQ_ID'] if post['ACQ_ID'] else ''
					        			payment_id.cancel()
					        			payment_id.action_draft()
					        			payment_id.amount = invoice_id.amount_total
					        			payment_id.payment_transaction_id=payment_transaction_id.id
					        			payment_id.post()
					        			move_line = request.env['account.move.line'].sudo().search(
											[('payment_id', '=', payment_id.id), ('credit', '!=', 0)])
					        			if move_line:
					        				add = invoice_id.register_payment(move_line)
					        return request.render("payment_paycaps.paycaps_confirmation_link_template",{'invoice_id':invoice_id})
					    else:
					        context = {"active_model": 'sale.order', "active_ids": [order.id], "active_id": order.id}
					        amount = int(post['AMOUNT'])/100

					        for line in order.order_line:
					            print('order line product name :',line.product_id.name,line.product_id.id,line.product_id.invoice_policy)
					            if line.product_id.invoice_policy != 'order':
					                print('In Iffffff')
					                product = request.env['product.product'].sudo().browse(line.product_id.id)
					                print('product',product)
					                product.write({'invoice_policy' : 'order'})
					                print('product.invoice_policy',product.invoice_policy)

					        order.action_confirm()

					        # Now create invoice.
					        payment = http.request.env['sale.advance.payment.inv'].sudo().create({
					            'advance_payment_method': 'all',
					            'amount': amount,
					        })
					        if not order.invoice_ids:
					            invoice = payment.with_context(context).create_invoices()
					            for invoice in order.invoice_ids:
					                invoice.with_context(context).action_invoice_open()
					                invoice.with_context(context).pay_and_reconcile(
					                    http.request.env['account.journal'].sudo().search([('id', '=', payment_type)]), amount)
					            if invoice :
					                payment_id=request.env['account.payment'].sudo().search([('invoice_ids','in',invoice.id)],limit=1)
					                if payment_id:
					                	payment_transaction_id=request.env['payment.transaction'].sudo().search([('invoice_ids','in',invoice.id)],limit=1)#request.env['payment.transaction'].sudo().search([('reference','=',reference)],limit=1)
					                	if payment_transaction_id:
					                		payment_transaction_id.payment_id=payment_id.id
					                		payment_transaction_id.state='done'
					                		#payment_transaction_id.acquirer_reference=post['ACQ_ID'] if post['ACQ_ID'] else ''
					                		payment_id.cancel()
					                		payment_id.action_draft()
					                		payment_id.amount=invoice.amount_total
					                		payment_id.post()

					        request.website.sale_reset()

					    return request.render("payment_paycaps.paycaps_confirmation", {'order': order,'invoice':order.invoice_ids})

		else:
			print("###########3333333222222222222")
			if request.session['sale_last_order_id']:
				print("COD And wire transfer",)
				order = request.env['sale.order'].sudo().browse(request.session['sale_last_order_id'])
				return request.render("website_sale.confirmation", {'order': order})
			else:
				return request.redirect('/shop')



        
