from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ArchiveRequest(models.Model):
    _name = 'archive.request'
    _description = 'Тодорхойлолт бичүүлэх хүсэлт'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'request_type'
    _order = 'sequence asc'  # Шинэ нь дээрээ харагдана
    user_id = fields.Many2one('res.users', string='Хэрэглэгч', default=lambda self: self.env.user)

    # sequence-ийг readonly болгож, default-ыг нь авч хаялаа
    sequence = fields.Integer(string='Дд', readonly=True, copy=False)

    state = fields.Selection([
        ('new', 'Шинэ'),
        ('sent', 'Илгээсэн'),
        ('done', 'Олгосон')
    ], default='new', string='Төлөв', tracking=True)

    request_type = fields.Selection([
        ('certificate', 'Тодорхойлолт')
    ], string='Хүсэлтийн төрөл', default='certificate', readonly=True)

    z_code = fields.Char(string='Ажилтны Z code', required=True)
    organization = fields.Char(string='Хаана, ямар байгууллагад', required=True)
    about = fields.Text(string='Зориулалт', required=True)

    request_employee_id = fields.Many2one('hr.employee', string='Хүсэлт илгээсэн ажилтан',
                                          default=lambda self: self.env.user.employee_id)
    request_date = fields.Date(string='Хүсэлт илгээсэн огноо', default=fields.Date.context_today)

    email_to = fields.Char(string='Хүлээн авагчийн хаяг')
    approved_file = fields.Binary(string='Батлагдсан файл')
    sender_employee_id = fields.Many2one(
        'hr.employee', string='Илгээсэн ажилтан',
        default=lambda self: self.env.user.employee_id
    )
    send_date = fields.Datetime(string='Илгээсэн огноо', default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        # Хүсэлтийн төрлөөр шүүж тоолно
        r_type = vals.get('request_type')
        domain = [('request_type', '=', r_type)] if r_type else []

        max_seq = self.sudo().read_group(domain, ['sequence:max'], [])
        max_val = max_seq[0]['sequence'] if max_seq and max_seq[0]['sequence'] else 0

        vals['sequence'] = max_val + 1
        return super(ArchiveRequest, self).create(vals)

    def action_send_to_hr(self):
        template = self.env.ref('alban_blank.email_template_request_to_hr')
        for rec in self:
            rec.state = 'sent'
            template.send_mail(rec.id, force_send=True)

    def action_approve(self):
        template = self.env.ref('alban_blank.email_template_response_to_employee')
        for rec in self:
            if not rec.approved_file:
                raise ValidationError("Батлагдсан файлыг оруулна уу!")
            rec.sender_employee_id = self.env.user.employee_id
            rec.send_date = fields.Datetime.now()
            rec.state = 'done'
            template.send_mail(rec.id, force_send=True)