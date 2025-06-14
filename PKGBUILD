# Maintainer: Saeed Badrelden <saeedbadrelden2021@gmail.com.com>
pkgname=hel-process
pkgver=1.0
pkgrel=1
pkgdesc="Helwan Process Manager"
arch=('any')
url="https://github.com/helwan-linux/hel-process"
license=('MIT')
depends=('python' 'python-pyqt5' 'python-psutil' 'python-pyqtgraph')
makedepends=('git')
# تم تعديل رابط المصدر لاستخدام master.tar.gz لأنه متاح ويعمل.
source=("$pkgname-$pkgver.tar.gz::https://github.com/helwan-linux/hel-process/archive/master.tar.gz")
sha256sums=('SKIP') # يمكن تغييرها بعد تحميل المصدر وتوليد sha256

package() {
    # تم تعديل مسار الـ cd ليتناسب مع اسم المجلد الناتج من فك ضغط master.tar.gz
    # وهو الآن hel-process-main/hel-process-manager
    cd "$srcdir/hel-process-main/hel-process-manager"

    # أنشئ مجلد التثبيت
    install -dm755 "$pkgdir/usr/share/$pkgname"
    cp -r lang logo main.py "$pkgdir/usr/share/$pkgname/"

    # ملف التشغيل (launcher)
    # أنشئ ملف launcher مؤقت لضمان تشغيل main.py كسكريبت بايثون
    # هذا يحل مشكلة "ImportError" عن طريق تشغيل الملف مباشرة
    echo '#!/usr/bin/env python' > "$srcdir/hel-process-launcher"
    echo 'import os' >> "$srcdir/hel-process-launcher"
    echo 'import sys' >> "$srcdir/hel-process-launcher"
    echo "sys.path.insert(0, '/usr/share/$pkgname')" >> "$srcdir/hel-process-launcher"
    echo "os.execvpe('python', ['python', '/usr/share/$pkgname/main.py'] + sys.argv[1:], os.environ)" >> "$srcdir/hel-process-launcher"
    install -Dm755 "$srcdir/hel-process-launcher" "$pkgdir/usr/bin/hel-process"


    # أيقونة التطبيق
    install -Dm644 logo/icon.png "$pkgdir/usr/share/icons/hicolor/256x256/apps/hel-process.png"

    # ملف الديسكتوب
    # تأكد من وجود الملف ده في الـ source
    install -Dm644 helwan-process-manager.desktop "$pkgdir/usr/share/applications/hel-process.desktop"
}
