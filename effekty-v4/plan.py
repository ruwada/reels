"""Reel «17 эффектов» v4: 17 short takes (one effect each), filmed 2026-10-18 by the user in two seats:
A = facing the camera, green arch behind; B = side-on at the laptop with the plant and the coffee.
Each take: kept range (source seconds), seat, and the voice chunks = his own words on the spans his lips say them
(spans measured on the ElevenLabs-isolated take audio, spans.py).
Ranges keep ~0.13 s before his first word and ~0.15 s after his last one, so the takes play as one flowing speech."""
SRC = "/tmp/fx/v4/{}.mov"
FPS = 30

TAKES = [
    # take, a, b, seat, voice chunks (text, lip start, lip end)
    ("0342", 3.75, 9.52, "A", [("Монтажёр делал бы", 3.85, 5.05), ("такие эффекты", 5.08, 5.95), ("неделю,", 5.98, 6.53),
                                ("а я делаю", 6.91, 7.80), ("с и-и,", 7.90, 8.32), ("пока пью кофе.", 8.42, 9.24)]),
    ("0343", 5.83, 10.75, "A", [("Ищешь монтажёра,", 5.96, 6.89), ("ждёшь", 7.42, 7.80), ("правки,", 7.90, 8.34), ("платишь за каждый эффект?", 9.13, 10.37)]),
    ("0344", 1.85, 5.33, "A", [("А можно так:", 1.98, 2.61), ("твои ролики", 3.05, 3.78), ("летают вокруг тебя.", 4.02, 5.10)]),
    ("0346", 1.73, 4.60, "A", [("Главное слово — стеклом прямо на стене.", 1.86, 4.38)]),
    ("0348", 1.57, 4.12, "A", [("Комната уезжает,", 1.70, 2.73), ("прямо как в кино.", 3.04, 3.92)]),
    ("0349", 2.34, 4.52, "A", [("Ты", 2.47, 2.94), ("на обложке журнала.", 3.18, 4.33)]),
    ("0351", 1.59, 4.86, "A", [("Фон меняется по щелчку,", 1.72, 3.34), ("без зелёной ткани.", 3.61, 4.57)]),
    ("0352", 1.25, 3.10, "A", [("Вокруг оживают рисунки.", 1.38, 2.83)]),
    ("0354", 1.58, 4.19, "A", [("Или ты —", 1.71, 2.28), ("коллаж из бумаги.", 2.82, 3.96)]),
    ("0355", 1.42, 4.27, "A", [("Стена за спиной заполняется твоими роликами.", 1.55, 4.06)]),
    ("0356", 1.42, 4.94, "A", [("Наезд", 1.55, 2.08), ("на", 2.47, 2.70), ("каждое", 2.72, 3.36), ("твоё", 3.58, 3.95), ("слово.", 4.15, 4.80)]),
    ("0358", 0.83, 3.07, "A", [("Охваты растут прямо за спиной.", 0.96, 2.85)]),
    ("0359", 0.97, 3.10, "A", [("Пролетаем сквозь кадр.", 1.10, 2.84)]),
    ("0364", 2.69, 5.20, "B", [("Я просто пишу ассистенту, что мне нужно.", 2.82, 4.99)]),
    ("0365", 1.80, 5.48, "B", [("Субтитры, звук, обложка —", 1.93, 3.68), ("всё монтируется само.", 4.37, 5.60)]),
    ("0366", 4.59, 7.85, "B", [("А", 4.72, 4.90), ("всё это", 5.00, 5.46), ("просто окно на моём ноутбуке.", 5.86, 7.35)]),
    ("0368", 4.17, 11.20, "B", [("Хочешь такие эффекты в своих роликах?", 4.30, 6.21),
                                ("Забирай гайд под номером восемнадцать в телеграме,", 6.55, 8.92),
                                ("ссылка в шапке профиля.", 9.68, 10.72)]),
]
REF = {"A": "0342", "B": "0364"}   # colour reference take per seat


def frames_of(a, b):
    return round(a * FPS), round(b * FPS)


def T(take, t):
    """Source time of a take -> reel timeline."""
    acc = 0.0
    for tk, a, b, *_ in TAKES:
        fa, fb = frames_of(a, b)
        if tk == take:
            t = min(max(t, fa / FPS), fb / FPS)   # a cue before the kept range fires at its first frame
            return round(acc + t - fa / FPS, 4)
        acc += (fb - fa) / FPS
    raise KeyError(take)


def start(take):
    return T(take, [x for x in TAKES if x[0] == take][0][1])


END = sum((frames_of(a, b)[1] - frames_of(a, b)[0]) / FPS for _, a, b, *_ in TAKES)


# v8: his picture is retimed to the clone voice (retime.py); when work/warp.json exists, T/start/END follow it
import json as _json, os as _os
import numpy as _np
_WARP = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "work", "warp.json")
if _os.path.exists(_WARP):
    WARP = _json.load(open(_WARP))
    TAKES = [x for x in TAKES if x[0] in WARP]

    def T(take, t):
        w = WARP[take]
        return round(w["start"] + float(_np.interp(t, w["src"], w["out"])), 4)

    def start(take):
        return WARP[take]["start"]

    END = WARP["_end"]
