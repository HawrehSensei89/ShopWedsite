from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from store.models import Banner, Category, Product, Profile

CATS = [
 ("clothing", "پوشاک", "Clothing", "ri-t-shirt-line", [
  ("تی‌شرت مشکی ساده", "Classic Black T-Shirt", 450000, "👕"), ("هودی قرمز", "Red Hoodie", 1250000, "🧥"),
  ("شلوار جین", "Denim Jeans", 980000, "👖"), ("کفش کتانی", "Running Sneakers", 2100000, "👟"),
  ("کلاه کپ", "Baseball Cap", 280000, "🧢"), ("پیراهن مردانه", "Men's Shirt", 720000, "👔")]),
 ("phones", "گوشی", "Phones", "ri-smartphone-line", [
  ("گوشی هوشمند Nova X", "Nova X Smartphone", 18500000, "📱"), ("گوشی میان‌رده Pulse 5", "Pulse 5 Mid-range", 11200000, "📱"),
  ("گوشی اقتصادی Lite", "Lite Budget Phone", 6400000, "📲"), ("هندزفری بی‌سیم", "Wireless Earbuds", 1900000, "🎧"),
  ("شارژر سریع", "Fast Charger", 350000, "🔌"), ("قاب محافظ", "Protective Case", 190000, "🛡️")]),
 ("posters", "تابلو", "Posters", "ri-image-2-line", [
  ("تابلو طبیعت", "Nature Canvas", 1350000, "🏞️"), ("تابلو انتزاعی", "Abstract Art", 1600000, "🎨"),
  ("تابلو شهر شب", "City Night Print", 1100000, "🌃"), ("تابلو خوشنویسی", "Calligraphy Frame", 1450000, "🖼️"),
  ("تابلو گل", "Floral Canvas", 900000, "🌸"), ("تابلو فضا", "Space Poster", 780000, "🪐")]),
]

class Command(BaseCommand):
    help = "Load demo data"
    def handle(self, *a, **k):
        for i, (slug, fa, en, icon, prods) in enumerate(CATS):
            c, _ = Category.objects.get_or_create(slug=slug, defaults=dict(name_fa=fa, name_en=en, icon=icon, order=i))
            for nfa, nen, price, emoji in prods:
                Product.objects.get_or_create(name_en=nen, defaults=dict(
                    category=c, name_fa=nfa, price=price, emoji=emoji,
                    desc_fa=f"{nfa} با کیفیت عالی و ارسال سریع. (متن آزمایشی)",
                    desc_en=f"{nen}: great quality and fast delivery. (demo text)"))
        if not Banner.objects.exists():
            Banner.objects.bulk_create([
                Banner(title_fa="تخفیف ویژه پوشاک", title_en="Fashion Mega Sale", subtitle_fa="تا ۵۰٪ تخفیف روی منتخب لباس‌ها", subtitle_en="Up to 50% off selected styles", link="/shop/clothing/", emoji="👕", theme="red", order=0),
                Banner(title_fa="جدیدترین گوشی‌ها", title_en="Newest Phones", subtitle_fa="با گارانتی و پرداخت امن", subtitle_en="Warranty included, safe checkout", link="/shop/phones/", emoji="📱", theme="green", order=1),
                Banner(title_fa="تابلوهای دکوراتیو", title_en="Decor Posters", subtitle_fa="خانه‌ات را زیبا کن", subtitle_en="Make your home beautiful", link="/shop/posters/", emoji="🖼️", theme="dark", order=2)])
        call_command("create_admin")
        u, made = User.objects.get_or_create(username="demo@example.com", defaults=dict(email="demo@example.com"))
        if made:
            u.set_password("demo1234"); u.save()
        Profile.objects.get_or_create(user=u)
        self.stdout.write(self.style.SUCCESS("Done. demo user: demo@example.com / demo1234"))
