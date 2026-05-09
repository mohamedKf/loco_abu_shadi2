"""
LOCO Abu Shadi — Menu Seed
Run: python seed_menu.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from menu.models import Category, MenuItem

print("🔥 Seeding LOCO Abu Shadi menu...")

MenuItem.objects.all().delete()
Category.objects.all().delete()
print("✅ Cleared existing menu data")

cats = {}

data_cats = [
    {'name_ar': 'جابيتات',           'name_he': "ג'בטות",         'name': 'Jabatas',    'sort_order': 1},
    {'name_ar': 'باجيتات',           'name_he': 'באגטים',          'name': 'Baguettes',  'sort_order': 2},
    {'name_ar': 'مرتديلات وتوستات', 'name_he': 'טורטיות וטוסטים', 'name': 'Toasts',     'sort_order': 3},
    {'name_ar': 'البرجر',            'name_he': 'המבורגרים',       'name': 'Burgers',    'sort_order': 4},
    {'name_ar': 'وجبات سريعة',      'name_he': 'ארוחות מהירות',   'name': 'Fast Meals', 'sort_order': 5},
    {'name_ar': 'إضافات جانبية',    'name_he': 'תוספות',          'name': 'Sides',      'sort_order': 6},
    {'name_ar': 'سلطات',             'name_he': 'סלטים',           'name': 'Salads',     'sort_order': 7},
    {'name_ar': 'مشروبات',           'name_he': 'שתייה',           'name': 'Drinks',     'sort_order': 8},
]

for c in data_cats:
    cat = Category.objects.create(**c)
    cats[c['name_ar']] = cat
    print(f"  ✅ Category: {c['name_ar']}")

items = [
    # جابيتات
    {'cat': 'جابيتات', 'name_ar': 'جابيتا أسادو + شيبس',         'name_he': "ג'בטה אסאדו + צ'יפס",        'price': 70},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا دجاج + شيبس',          'name_he': "ג'בטה עוף + צ'יפס",          'price': 60},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا سلاسيسو + شيبس',       'name_he': "ג'בטה סלטיפו + צ'יפס",       'price': 60},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا سلاسيسو وعجل + شيبس',  'name_he': "ג'בטה סלטיפו ועגל + צ'יפס",  'price': 70},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا تونة + شيبس',          'name_he': "ג'בטה טונה + צ'יפס",         'price': 45},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا شنيتسل + شيبس',        'name_he': "ג'בטה שניצל + צ'יפס",        'price': 60},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا عجل + شيبس',           'name_he': "ג'בטה עגל + צ'יפס",          'price': 65},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا كرسي + شيبس',          'name_he': "ג'בטה קריספי + צ'יפס",       'price': 60},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا حلومة + شيبس',         'name_he': "ג'בטה חלומי + צ'יפס",        'price': 40},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا لوكو + شيبس',          'name_he': "ג'בטה לוקו + צ'יפס",         'price': 50},
    {'cat': 'جابيتات', 'name_ar': 'جابيتا حبش',                  'name_he': "ג'בטה פסטרמה",               'price': 35},

    # باجيتات
    {'cat': 'باجيتات', 'name_ar': 'باجيت دجاج + شيبس',           'name_he': "באגט עוף + צ'יפס",           'price': 50},
    {'cat': 'باجيتات', 'name_ar': 'باجيت أسادو + شيبس',          'name_he': "באגט אסאדו + צ'יפס",         'price': 60},
    {'cat': 'باجيتات', 'name_ar': 'باجيت عجل + شيبس',            'name_he': "באגט עגל + צ'יפס",           'price': 60},
    {'cat': 'باجيتات', 'name_ar': 'باجيت حلومة + شيبس',          'name_he': "באגט חלומי + צ'יפס",         'price': 35},
    {'cat': 'باجيتات', 'name_ar': 'باجيت شنيتسل + شيبس',         'name_he': "באגט שניצל + צ'יפס",         'price': 50},
    {'cat': 'باجيتات', 'name_ar': 'باجيت سلاسيسو وعجل + شيبس',   'name_he': "באגט סלטיפו ועגל + צ'יפס",   'price': 65},
    {'cat': 'باجيتات', 'name_ar': 'باجيت سلاسيسو + شيبس',        'name_he': "באגט סלטיפו + צ'יפס",        'price': 60},
    {'cat': 'باجيتات', 'name_ar': 'باجيت كرسي + شيبس',           'name_he': "באגט קריספי + צ'יפס",        'price': 50},
    {'cat': 'باجيتات', 'name_ar': 'باجيت لوكو',                  'name_he': "באגט לוקו + צ'יפס",          'price': 45},

    # مرتديلات وتوستات
    {'cat': 'مرتديلات وتوستات', 'name_ar': 'توست أجبان',         'name_he': 'טוסט גביות',                 'price': 35},
    {'cat': 'مرتديلات وتوستات', 'name_ar': 'باشكا عجة',          'name_he': "באשקה עג'ה",                 'price': 35},
    {'cat': 'مرتديلات وتوستات', 'name_ar': 'باشكا',              'name_he': 'באשקה',                      'price': 30},
    {'cat': 'مرتديلات وتوستات', 'name_ar': 'كرسي تشيز',          'name_he': 'קריספי צייז',                'price': 50},
    {'cat': 'مرتديلات وتوستات', 'name_ar': 'مرتديلا',            'name_he': 'מורצדלה',                    'price': 45},
    {'cat': 'مرتديلات وتوستات', 'name_ar': 'بيج امستردام',       'name_he': 'ביג אמסטרדם',                'price': 45},

    # البرجر
    {'cat': 'البرجر', 'name_ar': 'سماش برجر',                    'name_he': 'סמאש בורגר',                 'price': 70},
    {'cat': 'البرجر', 'name_ar': 'كرسي برجر',                    'name_he': 'קריספי בורגר',               'price': 50},
    {'cat': 'البرجر', 'name_ar': 'برجر كلاسيك',                  'name_he': 'בורגר קלאסי',                'price': 50},
    {'cat': 'البرجر', 'name_ar': 'برجر مخبوز',                   'name_he': 'בורגר אפוי',                 'price': 80},
    {'cat': 'البرجر', 'name_ar': 'تشيز برجر',                    'name_he': "צ'יז בורגר",                 'price': 80},

    # وجبات سريعة
    {'cat': 'وجبات سريعة', 'name_ar': 'هوت دوج',                 'name_he': 'הוט דוג',                    'price': 25},
    {'cat': 'وجبات سريعة', 'name_ar': 'شنيتسل هوت دوج',          'name_he': 'שניצל הוט דוג',              'price': 15},
    {'cat': 'وجبات سريعة', 'name_ar': 'رغيف كباب + شيبس',        'name_he': "לחמנייה כבב + צ'יפס",        'price': 35},

    # إضافات جانبية
    {'cat': 'إضافات جانبية', 'name_ar': 'شيبس',                  'name_he': "צ'יפס",                      'price': 15},
    {'cat': 'إضافات جانبية', 'name_ar': 'كدوري فيرة',            'name_he': 'כדורי פירה',                 'price': 25},
    {'cat': 'إضافات جانبية', 'name_ar': 'شيبس بتاتا',            'name_he': "צ'יפס בטטה",                 'price': 25},
    {'cat': 'إضافات جانبية', 'name_ar': 'بوتيتو',                'name_he': 'פוטטוס',                     'price': 25},
    {'cat': 'إضافات جانبية', 'name_ar': 'بطاطا حلوة',            'name_he': 'בטטה',                       'price': 25},

    # سلطات
    {'cat': 'سلطات', 'name_ar': 'فتوش',                          'name_he': 'פטוש',                       'price': 35},
    {'cat': 'سلطات', 'name_ar': 'سلطة لوكو فيله',                'name_he': 'סלט לוקו פילה',              'price': 50},
    {'cat': 'سلطات', 'name_ar': 'تبولة',                         'name_he': 'טאבולה',                     'price': 35},

    # مشروبات
    {'cat': 'مشروبات', 'name_ar': 'كولا',                        'name_he': 'קולה',                       'price': 7},
    {'cat': 'مشروبات', 'name_ar': 'كولا زجاجة',                  'name_he': 'קולה זכוכית',                'price': 10},
]

for item_data in items:
    cat_name = item_data.pop('cat')
    item_data['category']     = cats[cat_name]
    item_data['is_available'] = True
    item_data['name']         = item_data['name_he']
    MenuItem.objects.create(**item_data)

print(f"\n🔥 Done! Created {len(items)} items across {len(cats)} categories.")