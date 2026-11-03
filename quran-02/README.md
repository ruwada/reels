# quran-02 — видео с чтением Корана

Полное описание вида монтажа, правил и источников — [`../docs/MONTAZH-VIDY.md`](../docs/MONTAZH-VIDY.md#4-чтение-корана).

**Главное правило: ни арабский текст, ни перевод, ни разбивка не придумываются и не правятся.**
Всё приходит готовым из quran.com (перевод Кулиева, id 45) со сверкой по alquran.cloud, аудио и
тайминг аятов — с mp3quran.net. Один аят целиком на экран. Падение сверки в `fetch.py` = стоп.

    python3 fetch.py <имя> <id чтеца> <сура> <с аята> <по аят>   # src/<имя>/ayat.json + mp3
    python3 make.py <cfg.json>                                   # build.py + contrast.py, до 5 попыток

`cfg.json`: `{"name", "style": "glass|clean|bottom", "surah_name", "clips": [[pexelsId, ss, dur], ...]}`

- `build.py` — сдвигает границы аятов к ближайшей паузе (±1 с), собирает слои и видео
- `layers.mjs` — слои текста в Playwright (Amiri Quran / Scheherazade New / Cormorant Garamond / Manrope)
- `contrast.py` — WCAG-контраст субтитров против фона, порог 4.5, выход 1 при провале
- `make.py` — цикл сборки с затемнением подложки провалившихся аятов
- `check_timing.py` — отчёт по громкости на границах аятов

Чтецы (чередуем): 92 ад-Доссари, 86 аль-Катами, 12 Абкар, 217 Балила, 245 ас-Салими, 259 ан-Нуфайс.
`src/*/*.mp3` и `work/` в git не идут.
