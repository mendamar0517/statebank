from odoo import http
from odoo.http import request

class ProfileDashboardController(http.Controller):
    @http.route('/get_profile_dashboard_data', type='json', auth='user')
    def get_data(self):
        # sudo() ашиглан хэрэглэгч болон ажилтны мэдээллийг найдвартай уншина
        user = request.env.user.sudo()
        employee = user.employee_id.sudo()

        # Бүх топ цэсүүд
        all_top_menus = request.env['ir.ui.menu'].sudo().search([('parent_id', '=', False)])
        available_modules = sorted([m.name for m in all_top_menus])

        menu_hierarchy = {}

        for menu in all_top_menus:
            sub_menus_list = []
            total_module_count = 0

            # Тухайн топ цэс доорх бүх навч цэсүүд
            child_menus = request.env['ir.ui.menu'].sudo().search([
                ('parent_id', 'child_of', menu.id),
                ('action', '!=', False)
            ])

            for sub in child_menus:
                if sub.action._name == 'ir.actions.act_window':
                    res_model = sub.action.res_model
                    if res_model in request.env:
                        Model = request.env[res_model]
                        # Зөвхөн хэрэглэгч өөрөө унших эрхтэй моделиудыг авна
                        if Model.check_access_rights('read', raise_exception=False):
                            count = 0
                            records = []
                            if 'create_uid' in Model._fields:
                                # Миний үүсгэснийг тоолох
                                count = Model.search_count([('create_uid', '=', user.id)])
                                if count > 0:
                                    records_raw = Model.search([('create_uid', '=', user.id)], limit=10)
                                    for rec in records_raw:
                                        records.append({
                                            'id': rec.id,
                                            'display_name': rec.display_name or Model._description
                                        })

                            # ЗАСВАР: Бичлэг 0 байсан ч цэсийг нэмнэ (ингэснээр цэс нэмэх хэсэгт харагдана)
                            sub_menus_list.append({
                                'id': sub.id,
                                'name': str(sub.name),
                                'model': res_model,
                                'count': count,
                                'records': records,
                                'has_status': any(f in Model._fields for f in ['state', 'stage_id', 'x_state'])
                            })
                            total_module_count += count

            if sub_menus_list:
                menu_hierarchy[str(menu.name)] = {
                    'subs': sub_menus_list,
                    'total': total_module_count
                }

        # Эрэмбэлэлт: Бичлэг ихтэйг нь эхэнд, дараа нь нэрээр нь
        sorted_keys = sorted(menu_hierarchy.keys(), key=lambda k: (menu_hierarchy[k]['total'], k), reverse=True)

        # ERP эрхүүдийг sudo-оор авах
        erp_rights = []
        for g in user.groups_id:
            if g.category_id:
                erp_rights.append(f"{g.category_id.name}: {g.name}")

        image_base64 = False
        if employee and employee.image_1920:
            # Odoo-ийн зураг binary хэлбэрээр байдаг тул string болгож хөрвүүлнэ
            image_base64 = employee.image_1920.decode('ascii')

        return {
            'user_info': {
                'name': user.name,
                'email': user.login,
                'job': employee.job_id.name or 'Албан тушаалгүй' if employee else 'Мэдээлэлгүй',
                'dept': employee.department_id.name or 'Хэлтэсгүй' if employee else 'Мэдээлэлгүй',
                'phone': employee.work_phone or 'Мэдээлэлгүй' if employee else '',
                'image': image_base64,  # Зассан хэсэг
            },
            'erp_rights': sorted(list(set(erp_rights))),
            'menu_hierarchy': menu_hierarchy,
            'default_visible': sorted_keys[:5] if sorted_keys else available_modules[:5],
            'available_modules': available_modules
        }

    @http.route('/get_sub_menu_analytics', type='json', auth='user')
    def get_analytics(self, res_model):
        user = request.env.user
        Model = request.env[res_model]
        status_data = {}

        f_name = next((f for f in ['state', 'stage_id', 'x_state'] if f in Model._fields), False)
        if f_name:
            groups = Model.read_group([('create_uid', '=', user.id)], [f_name], [f_name])
            for g in groups:
                label = "Тодорхойгүй"
                if g[f_name]:
                    label = str(g[f_name][1] if isinstance(g[f_name], tuple) else g[f_name])
                status_data[label] = g[f'{f_name}_count']

        created = Model.search_count([('create_uid', '=', user.id)])
        assigned = Model.search_count([('user_id', '=', user.id)]) if 'user_id' in Model._fields else 0

        return {
            'status': status_data,
            'participation': {'Үүсгэгч': created, 'Оролцогч': assigned}
        }