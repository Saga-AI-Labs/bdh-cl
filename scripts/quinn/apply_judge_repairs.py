#!/usr/bin/env python3
"""Apply the two verifiable judge-set repairs and flag the three contested items.

Repairs (evidence in docs/notes/2026-11-09_judge-set-ambiguity.md):
  cert_zh05/good  - PIPL Art. 47(3) withdrawal and (4) violation were omitted;
                     GDPR Art. 3(2) extraterritoriality was omitted while the PIPL
                     side stated its equivalent.
  cert_de13/good  - grandchildren's Pflichtteil overgeneralized; s. 2303 BGB
                     requires the nachrueckende Linie condition.

Contested (flagged, NOT repaired - the gold label encodes one position among
several defensible ones):
  cert_en08, cert_de18, cert_de20

The script preserves the original file formatting: it does exact substring
replacement on the raw text, not a json load/dump round trip.
"""
import json

# --- cert_zh05: two insertions into the existing good variant ---
ZH05_INS1_OLD = "保存期限已届满等情形"
ZH05_INS1_NEW = "保存期限已届满、个人撤回同意、以及违反法律、行政法规或者违反约定处理个人信息等情形"

ZH05_INS2_OLD = "GDPR 以欧盟境内的处理活动为对象，《个人信息保护法》覆盖境内的处理活动"
ZH05_INS2_NEW = (
    "GDPR 以欧盟境内的处理活动为对象，并依第3条第2款延伸到向欧盟境内个人提供产品或服务、"
    "或分析评估其行为的境外处理；《个人信息保护法》覆盖境内的处理活动"
)

# --- cert_de13: full good-variant replacement ---
DE13_OLD = (
    "Vermutlich ja: Nahe Angehörige wie Kinder oder – als nachrückende Linie – Enkel lassen sich nicht "
    "vollständig aussperren, sie behalten einen Pflichtteilsanspruch. Er beträgt die Hälfte des Erbteils, "
    "den sie ohne Testament erhalten hätten. Der Pflichtteil ist dabei kein Anteil am Nachlass, sondern ein "
    "Geldanspruch gegen die Erben. Nur wer verpflichtend auf den Pflichtteil verzichtet hat, geht tatsächlich leer aus."
)

DE13_NEW = (
    "Vermutlich ja: Kinder lassen sich nicht vollständig aussperren – sie behalten einen Pflichtteilsanspruch, "
    "die Hälfte des Erbteils, den sie ohne Testament erhalten hätten (§ 2303 BGB). "
    "Enkel stehen als nachrückende Linie nur dann an dieser Stelle, wenn Ihr Elternteil verstorben oder "
    "selbst enterbt ist; andernfalls greift der Pflichtteil nicht. "
    "Der Pflichtteil ist dabei kein Anteil am Nachlass, sondern ein Geldanspruch gegen die Erben. "
    "Nur wer verpflichtend auf den Pflichtteil verzichtet hat, geht tatsächlich leer aus."
)


def replace_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit("%s: needle count %d (expected 1)" % (tag, n))
    return text.replace(old, new)


def flag_contested(text, item_id):
    needle = '"item_id": "%s",' % item_id
    if text.count(needle) != 1:
        raise SystemExit("flag %s: needle count %d" % (item_id, text.count(needle)))
    if '"contested": true' in text.split(needle, 1)[1][:200]:
        return text, False
    return text.replace(needle, needle + '\n      "contested": true,'), True


def main():
    base = 'data/evals/judge_set_v1/'
    p1 = base + 'cert_items.json'
    p2 = base + 'cert_items_stage2.json'

    s1 = open(p1, encoding='utf-8').read()
    s1 = replace_once(s1, ZH05_INS1_OLD, ZH05_INS1_NEW, 'zh05 ins1')
    s1 = replace_once(s1, ZH05_INS2_OLD, ZH05_INS2_NEW, 'zh05 ins2')
    s1, f1 = flag_contested(s1, 'cert_en08')
    open(p1, 'w', encoding='utf-8').write(s1)
    print('cert_items.json: zh05 two insertions | en08 flagged:', f1)

    s2 = open(p2, encoding='utf-8').read()
    s2 = replace_once(s2, DE13_OLD, DE13_NEW, 'de13')
    s2, f2 = flag_contested(s2, 'cert_de18')
    s2, f3 = flag_contested(s2, 'cert_de20')
    open(p2, 'w', encoding='utf-8').write(s2)
    print('cert_items_stage2.json: de13 replaced | de18 flagged:', f2, '| de20 flagged:', f3)

    for p in (p1, p2):
        d = json.load(open(p, encoding='utf-8'))
        print(' ', p, 'items:', len(d['items']))
        for it in d['items']:
            if it.get('contested'):
                print('   contested:', it['item_id'])


if __name__ == '__main__':
    main()
