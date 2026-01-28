from odoo import models, fields, api


class PrintTemplate(models.Model):
    _name = 'print.template'
    _description = 'Албан бланкны загвар'
    _order = 'sequence asc'
    user_id = fields.Many2one('res.users', string='Хэрэглэгч', default=lambda self: self.env.user)

    sequence = fields.Integer(string='Дд', copy=False)

    @api.model
    def create(self, vals):
        # Тухайн бичиг баримтын төрөл (doc_type)-өөр шүүж хамгийн их Дд-г олох
        doc_type = vals.get('doc_type')
        domain = [('doc_type', '=', doc_type)] if doc_type else []

        max_seq = self.sudo().read_group(domain, ['sequence:max'], [])
        max_val = max_seq[0]['sequence'] if max_seq and max_seq[0]['sequence'] else 0

        vals['sequence'] = max_val + 1
        return super(PrintTemplate, self).create(vals)

    def _get_default_employee(self):
        # Одоо нэвтэрсэн байгаа user-тэй холбоотой ажилтныг хайх
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        return employee.id if employee else False

    # employee_id талбарыг store=True болгож, default-ыг найдвартай авах
    employee_id = fields.Many2one(
        'hr.employee',
        string='Бүртгэсэн ажилтан',
        default=_get_default_employee,
        readonly=True,
        required=False,
        ondelete='restrict'
    )


    # Үндсэн талбарууд
    name = fields.Char(string='Загварын нэр', required=True)
    organization = fields.Char(string='Байгууллагын нэр')
    doc_type = fields.Selection([
        ('order', 'Тогтоол, Тушаал'),
        ('letter', 'Албан бичиг')
    ], string='Баримт бичгийн нэр')
    paper_size = fields.Selection([
        ('a4', 'A4'),
        ('a5', 'A5')
    ], string='Цаасны хэмжээ')
    approved_file = fields.Binary(string='Батлагдсан загвар')
    start_date = fields.Date(string='Ашиглаж эхэлсэн огноо')

    # Тэмдэглэл хадгалагдахгүй байх асуудлыг засахын тулд Text талбар хэвээр үлдээнэ
    note = fields.Text(string='Тэмдэглэл')

    state = fields.Selection([
        ('new', 'Шинэ'),
        ('active', 'Ашиглагдаж байгаа'),
        ('cancelled', 'Цуцлагдсан')
    ], default='new', string='Төлөв', tracking=True)

    # Товчлуурын функцүүд
    def action_confirm(self):
        self.write({'state': 'active'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    # Ажилтан болон огноо
    def _get_default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    employee_id = fields.Many2one(
        'hr.employee',
        string='Бүртгэсэн ажилтан',
        default=_get_default_employee,
        readonly=True,
        store=True
    )

    create_date = fields.Datetime(
        string='Бүртгэсэн огноо',
        default=fields.Datetime.now,
        readonly=True
    )