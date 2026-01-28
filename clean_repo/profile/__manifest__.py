{
    'name': 'User Profile Dashboard',
    'version': '16.0.1.0',
    'category': 'Tools',
    'summary': 'Хэрэглэгчийн төсөл, сургалт болон хувийн мэдээллийн нүүр хуудас',
    'depends': ['base', 'hr', 'project'],
    'data': [
        'views/profile_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'profile/static/src/css/profile.css',
            'profile/static/src/js/profile.js',
            'profile/static/src/xml/profile.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}