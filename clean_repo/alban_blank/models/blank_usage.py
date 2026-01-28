from odoo import models, fields, api


class BlankUsage(models.Model):
    _name = 'blank.usage'
    _description = 'Албан бланкны ашиглалт'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Дд', default=1)
    blank_id = fields.Many2one('print.template', string='Албан бланкын нэр', required=True)
    received_date = fields.Date(string='Хүлээж авсан огноо', default=fields.Date.context_today)
    received_number = fields.Integer(string='Хүлээж авсан тоо')
    start_number = fields.Integer(string='Эхлэх дугаар')
    finish_number = fields.Integer(string='Дуусах дугаар')

    user_dep_id = fields.Many2one('hr.department', string='Ашиглаж байгаа нэгж',
                                  default=lambda self: self.env.user.employee_id.department_id)
    user_emp_id = fields.Many2one('hr.employee', string='Ашиглаж байгаа ажилтан',
                                  default=lambda self: self.env.user.employee_id)

    # Автомат талбарууд (Auto)
    created_emp = fields.Char(string='Бүртгэсэн ажилтан', default=lambda self: self.env.user.name, readonly=True)
    created_date = fields.Datetime(string='Бүртгэсэн огноо', default=fields.Datetime.now, readonly=True)

    @api.model
    def create(self, vals):
        # Сонгосон бланк (blank_id)-аар шүүж, тухайн бланк доторх MAX дугаарыг авна
        blank_id = vals.get('blank_id')
        domain = [('blank_id', '=', blank_id)] if blank_id else []

        max_seq = self.sudo().read_group(domain, ['sequence:max'], [])
        max_val = max_seq[0]['sequence'] if max_seq and max_seq[0]['sequence'] else 0

        vals['sequence'] = max_val + 1
        return super(BlankUsage, self).create(vals)