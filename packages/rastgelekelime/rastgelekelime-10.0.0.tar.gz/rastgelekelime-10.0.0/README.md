# rastgelekelime

[![PyPI](https://img.shields.io/badge/PyPI-blue?logo=PyPI&style=flat-square)](https://pypi.org/project/rastgelekelime)
[![GitHub](https://img.shields.io/badge/GitHub-black?logo=GitHub&style=flat-square)](https://github.com/EnesKeremAYDIN/pip-rastgelekelime)

## Bir yada daha fazla Türkçe kelime çıktısı alın.

Kurulum:

    pip install rastgelekelime

Kullanım:

    from rastgelekelime import words

    print(words())  # Bir adet çıktı almanızı sağlar.

    print(words(5))  # Belirlediğiniz kadar (Örn:5) çıktı almanızı sağlar.

    print(words({'min': 3, 'max': 10}))  # Belirli sayı aralığı kadar (örn: 3-10 arası) çıktı almanızı sağlar.

    print(words({'exactly': 2}))  # Kesinlikle belirlediğiniz kadar (örn: 2) çıktı almanızı sağlar.

    print(words({'exactly': 5, 'join': ' '}))  # Kesinlikle belirlediğiniz kadar (örn: 5) çıktı almanızı sağlar. Çıktı alınan kelimelerin arasına belirlediğiniz karakteri (örn: boşluk) koyar.

    print(words({'exactly': 5, 'join': ''}))  # Kesinlikle belirlediğiniz kadar (örn: 5) çıktı almanızı sağlar. Çıktı alınan kelimelerin arasına bir şey koymaz, yapışık çıktı verir.

    print(words({'exactly': 5, 'maxLength': 4}))  # Kesinlikle belirlediğiniz kadar (örn: 5) çıktı almanızı sağlar. En fazla belirlediğiniz uzunlukta (örn: 4) çıktı almanızı sağlar.

    print(words({'exactly': 5, 'wordsPerString': 2}))  # Kesinlikle belirlediğiniz kadar (örn: 5) çıktı almanızı sağlar. Alınan çıktının yanında kaç adet çıktı olmasını (örn: 2) seçmenizi sağlar.

    print(words({'exactly': 5, 'wordsPerString': 2, 'separator': '-'}))  # Kesinlikle belirlediğiniz kadar (örn: 2) çıktı almanızı sağlar. Alınan çıktının yanında kaç adet çıktı olmasını (örn: 2) seçmenizi sağlar. Çıktı alınan kelimelerin arasına belirlediğiniz karakteri (örn: -) koyar.

    print(words({'exactly': 5, 'wordsPerString': 2, 'formatter': lambda word, _: word.upper()}))  # Kesinlikle belirlediğiniz kadar (örn: 2) çıktı almanızı sağlar. Alınan çıktının yanında kaç adet çıktı olmasını (örn: 2) seçmenizi sağlar. Çıktıların tüm harflerini büyük harfle yazdırır.

    print(words({'exactly': 5, 'wordsPerString': 2, 'formatter': lambda word, index: word.capitalize() if index == 0 else word}))  # Kesinlikle belirlediğiniz kadar (örn: 2) çıktı almanızı sağlar. Alınan çıktının yanında kaç adet çıktı olmasını (örn: 2) seçmenizi sağlar. Çıktıların ilk harfini büyük yazdırır.

Bu paket, [random-words](https://pypi.org/project/random-words) üzerinde değişiklikler yapılarak oluşturulmuştur.
