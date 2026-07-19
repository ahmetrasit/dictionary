#!/usr/bin/env python3
"""Render the Turkish sirat example from the frozen root packet."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from textwrap import dedent


PROJECT = Path(__file__).resolve().parents[2]
PACKET_PATH = PROJECT / "data/output/root_packets/root_000858.json"
OUTPUT_PATH = Path(__file__).with_name("root_000858.tr.example.md")


EDITORIAL = dedent(
    """\
    # ص ر ط (ṣ-r-ṭ): Türkçe ansiklopedi maddesi örneği

    > Bu dosya, v2 ürün biçimini sınamak için hazırlanmış tam kapsamlı bir örnektir; kanonik ve son editoryal madde değildir. Arapça dal sınırları ve kimlikler donmuş V4 verisinden, Türkçe karşılık ve hata değerlendirmeleri ise gözden geçirilmesi gereken editoryal yargılardan gelir. Kur'an kullanımları hiçbir dala veya anlama atanmaz.

    - Kök zarfı: `root_000858`
    - Kök: `ص ر ط` (ṣ-r-ṭ)
    - Donmuş dal sayısı: 3
    - Kur'an gözlemevi: 45 morfem, 45 kelime, 45 ayet, 25 sure

    ## Kök profili

    `ص ر ط` (ṣ-r-ṭ), yol, geçiş sırasında kaybolma imgesiyle yutma ve darbede kesip geçen kılıç olmak üzere üç belirgin sözlük dalına ayrılan çok anlamlı bir köktür. Meḳâyîs ilk iki dal arasında iştikak bağı kuran bir görüş aktarır; ancak bu, bütün kaynakların paylaştığı kesin bir radyal çözümleme değil, kaynakla sınırlandırılması gereken bir açıklamadır. Mevcut envanter kolokasyon ağırlıklı değil, biçim ağırlıklıdır.

    | Dal | Arapça dal imgesi | Kısa yönlendirme |
    |---|---|---|
    | `root_000858/B001` | `الطريق المستقيم` (eṭ-ṭarîḳ el-müstaḳîm) | Yol, özellikle dosdoğru yol |
    | `root_000858/B002` | `الغيبة في المرور والبلع` (el-ğaybetü fi'l-mürûri ve'l-belʿi) | Yutulan şeyin geçişte kaybolması |
    | `root_000858/B003` | `السيف القاطع الماضي في الضربة` (es-seyfü'l-ḳâṭıʿu el-mâḍî fi'ḍ-ḍarbeti) | Darbede kesip geçen kılıç |

    ## B001: Yol, özellikle dosdoğru yol

    **Dal kimliği:** `root_000858/B001`

    **Kısa tanım:** `صِرَاط` (ṣirâṭ), `سِرَاط` (sirâṭ) ve `زِرَاط` (zirâṭ) biçimleriyle yolu, kaynaklarda özellikle `الطريق المستقيم` (eṭ-ṭarîḳ el-müstaḳîm), yani dosdoğru yolu ifade eder.

    **Kaynak tartışması:** Ṣıḥâḥ üç ünsüz değişkesini birlikte `الطريق` (eṭ-ṭarîḳ), “yol” diye tanımlar. Müfredât `الطريق المستقيم` (eṭ-ṭarîḳ el-müstaḳîm), “dosdoğru yol” niteliğini öne çıkarır. Meḳâyîs ṣ ile başlayan biçimi ibdâl başlığı altında yine yol olarak verir; başka bir başlıkta ise bazı âlimlerin, yolda ilerleyenin gözden kaybolmasıyla yutulan şeyin geçişte kaybolması arasında iştikak bağı kurduğunu bildirir.

    **İhtilaf:** Açık bir sözlük ihtilafı yoktur. Fark, Ṣıḥâḥ'ın geniş “yol” tanımı, Müfredât'ın doğruluk niteliğini öne çıkarması ve Meḳâyîs'in ek iştikak açıklaması arasındadır.

    **Bağlı biçimler:** `الصراط` (eṣ-ṣirâṭ), `السراط` (es-sirâṭ), `الزراط` (ez-zirâṭ).

    ### Önerilen Türkçe karşılıklar

    | Sıra | Karşılık | Koruduğu | Kaybı veya eklemesi | Hata profili |
    |---|---|---|---|---|
    | 1, ana | **dosdoğru yol** | Yol imgesini ve doğruluk niteliğini birlikte korur. | Kaynaklardaki daha geniş yalın “yol” kullanımını daraltabilir; mecazî bağlamda fiziksel yol çağrışımını artırabilir. | Yakın karşılık; daralma riski |
    | 2, alternatif | **düz yol** | Yolun eğrilikten uzak oluşunu kısa biçimde verir. | Türkçedeki “engebesiz/düz satıh” çağrışımını ekleyebilir; mecazî doğruluk boyutunu zayıflatabilir. | Daralma ve çağrışım kayması |

    ### Karıştırılabilecek veya elenen karşılıklar

    | Karşılık | Neden ana listeye alınmadı? | Hata profili |
    |---|---|---|
    | **yol** | Doğruluk niteliğini görünmez kılar ve `سَبِيل` (sebîl) ile `طَرِيق` (ṭarîḳ) gibi komşuları aynı Türkçe söze yığar. | Daralma ve çakışma |
    | **doğru yol** | Kullanılabilir olsa da `doğru` kolayca yalnız “ahlâken/hükmen doğru” okunur; fiziksel doğruluk ile normatif doğruluk arasındaki seçimi çeviriye taşır. | Yer değiştirme riski |
    | **sırat** | Türkçe okura yol anlamını kendi başına açıklamaz; terimleşmiş “Sırat Köprüsü” çağrışımı Arapça dal sınırına ek anlam yükler. | Anlam kaydırmış alıntı; yalnız tanıma terimi |

    ### Arapça komşu ayrımları

    - `سَبِيل` (sebîl), **uzanıp gidilen yol / ulaştıran vasıta** (`root_000672/B001`): Bu dal yolun yanında bir şeye eriştiren sebep, bağlantı, çare veya vasıta uzanımını da içerir. `صِرَاط` (ṣirâṭ) dalının mevcut sınırı bu genel “ulaşma vasıtası” boyutunu içermez ve özellikle dosdoğru yol imgesini öne çıkarır.
    - `طَرِيق` (ṭarîḳ), **güzergâh / yol / yöntem** (`root_000932/B002`): Bu dal fiziksel güzergâhtan hâl, din, sünnet, grup ve tabaka gibi geniş uzanımlara açılır. `صِرَاط` (ṣirâṭ) mevcut kaynak sınırında bu yol-yöntem-tabaka ağını taşımaz.
    - `قَصْد` (ḳaṣd), **yolun ve yürüyüşün düzgünlüğü** (`root_001230/B002`): Burada odak yol adının kendisinden çok yolun, yürüyüşün veya işin düzgün ve ölçülü oluşudur. `صِرَاط` (ṣirâṭ) ise bu dalda doğrudan yol adıdır.

    ## B002: Yutulan şeyin geçişte kaybolması

    **Dal kimliği:** `root_000858/B002`

    **Kısa tanım:** `سَرَطَ الطَّعَامَ` (seraṭa'ṭ-ṭaʿâme), yiyeceği geçiş sırasında gözden kaybolacak biçimde yutmayı; bağlantılı türevler ise kolay yutulmayı ve geniş boğazı ifade eder.

    **Kaynak tartışması:** Meḳâyîs kökün s'li biçimini geçiş ve kaybolma imgesiyle açıklar: yiyecek yutulunca geçişte kaybolur. Aynı kaynak kolay yutulan bir tatlıyı `السِّرِطْرَاط` (es-siriṭrâṭ), geniş boğazlı kişiyi de sonundaki m harfini zait sayarak `السَّرْطَم` (es-sarṭam) ile ilişkilendirir. Harekeli harici sözlük tanıkları yutma fiilini doğrular; fakat nihai madde her harekeyi kendi tanığına bağlamalıdır.

    **İhtilaf:** Açık bir ihtilaf yoktur. Bununla birlikte dalın paket içindeki ana delili Meḳâyîs'tir; dolayısıyla kaynak çeşitliliği B001'e göre daha düşüktür ve bu durum maddede açıkça görünmelidir.

    **Bağlı biçimler:** `سرط الطعام` (seraṭa'ṭ-ṭaʿâm), `السرطراط` (es-siriṭrâṭ), `السرطم` (es-sarṭam).

    ### Önerilen Türkçe karşılıklar

    | Sıra | Karşılık | Koruduğu | Kaybı veya eklemesi | Hata profili |
    |---|---|---|---|---|
    | 1, ana | **yutup geçişte kaybettirme** | Yutma eylemini ve kaynakta kurulan geçişte kaybolma imgesini birlikte korur. | Doğal bir tek-sözcük karşılık değil, açıklayıcı bir söz grubudur; kolay yutulma ve geniş boğaz türevlerini tek başına kapsamaz. | Açıklayıcı yakın karşılık |
    | 2, alternatif | **yutmak** | Fiilin doğal Türkçe karşılığını verir. | Kaybolma imgesini, kolay yutulma ve geniş boğaz uzanımlarını görünmez kılar; Türkçedeki mecazî kabullenme anlamlarını çağırabilir. | Daralma |

    ### Karıştırılabilecek veya elenen karşılıklar

    | Karşılık | Neden ana listeye alınmadı? | Hata profili |
    |---|---|---|
    | **boğazdan geçirmek** | Geçişi korur, fakat yutma eylemini dolaylılaştırır ve dışarıdan geçirtme ettirgenliğini çağrıştırabilir. | Yer değiştirme |
    | **içine çekmek** | Kaybolma yönünü sezdirir; ancak emme, çekme veya içine alma mekanizması ekler. | Genişleme |
    | **kaybetmek** | Gözden kaybolmayı taşır, fakat yiyecek, boğaz ve yutma alanını bütünüyle siler. | Ağır yer değiştirme |

    ### Arapça komşu ayrımları

    - `بَلَعَ` (belaʿa), **yutmak / boğaza indirmek** (`root_000150/B001`): Bu dal nesneyi, suyu veya yiyeceği boğaza alma eylemini ve yutma yerini kapsar. `سَرَطَ` (seraṭa) dalı ise kaynak açıklamasında özellikle geçişte kaybolma imgesini, kolay yutulmayı ve geniş boğaz türevlerini birlikte taşır.
    - `سَاغَ` (sâğa), **boğazdan kolayca geçmek** (`root_000761/B001`): Burada ayırıcı eksen yutmanın gerçekleşmesinden çok yiyecek veya içeceğin boğazdan pürüzsüz ve kolay inişidir. `سَرَطَ` (seraṭa) eylem ve kaybolma merkezlidir; kolaylık bunun türev uzanımlarından biridir.
    - `زَقَمَ` (zeḳame), **boğaza ulaştırmak / lokmalamak** (`root_000636/B002`): Bu dal bir şeyi boğaza ulaştırma, aşırı içme veya hoş olmayan şeyi yutma gibi daha zorlayıcı uzanımlar taşır. `سَرَطَ` (seraṭa) için bu zorlama ve nahoşluk bileşenleri zorunlu değildir.

    ## B003: Darbede kesip geçen kılıç

    **Dal kimliği:** `root_000858/B003`

    **Kısa tanım:** `السُّرَاط` (es-sürâṭ), kesen, nüfuz eden ve darbede ilerleyen kılıç için kullanılan addır.

    **Kaynak tartışması:** Meḳâyîs'in harekesiz metni `السراط السيف القاطع الماضي في الضريبة` ifadesiyle sözü kesici ve darbede geçen kılıç olarak verir. Harekeli harici sözlük tanığı kılıç kullanımını `السُّرَاط` (es-sürâṭ), yol kullanımını ise `السِّرَاط` (es-sirâṭ) biçiminde ayırır. Bu hareke farkı, aynı ünsüz yazımın B001 ile karıştırılmasını önlediği için yayınlanan maddede korunmalıdır.

    **İhtilaf:** Açık bir ihtilaf yoktur; ancak bu dal paket içinde Meḳâyîs'in tekil tanıklığına dayanır. Harekeli harici tanık okunuşu doğrular, yeni bir dal sınırı kurmaz.

    **Bağlı biçim:** `السُّرَاط` (es-sürâṭ).

    ### Önerilen Türkçe karşılıklar

    | Sıra | Karşılık | Koruduğu | Kaybı veya eklemesi | Hata profili |
    |---|---|---|---|---|
    | 1, ana | **darbede kesip geçen kılıç** | Kılıcı, kesme gücünü ve darbede ilerleme tasvirini birlikte korur. | Tek sözcüklü doğal karşılık değil, kaynak imgesini açan bir söz grubudur. | Açıklayıcı yakın karşılık |
    | 2, alternatif | **keskin kılıç** | Nesneyi ve kesiciliği kısa, doğal biçimde verir. | Darbede ilerleme ve nüfuz boyutunu görünmez kılar; keskinlik kaynak ifadesinden daha genel okunabilir. | Daralma |

    ### Karıştırılabilecek veya elenen karşılıklar

    | Karşılık | Neden ana listeye alınmadı? | Hata profili |
    |---|---|---|
    | **kılıç** | Nesneyi verir, fakat dalı ayıran kesme ve darbede geçme niteliğini siler. | Daralma |
    | **keskin** | Bir nesne adı değildir; bıçak, dil, bakış veya zekâ gibi başka taşıyıcılara da gider. | Dilbilgisel kategori kayması ve genişleme |
    | **sırat** | Harekesi gösterilmediğinde Türkçedeki yol/ahiret terimiyle karışır ve kılıç anlamını açıklamaz. | Eş yazım ve alıntı çakışması |

    ### Arapça komşu ayrımları

    - `صَمْصَام` (ṣamṣâm), **eğilmeyen, kemiği geçen kesici kılıç** (`root_000884/B011`): Bu dal kılıcın eğilmemesi veya kemikten geçmesi üzerinde durur. `السُّرَاط` (es-sürâṭ) dalının belirgin kaynak tasviri ise kılıcın darbede kesip ilerlemesidir.
    - `حَدّ` (ḥadd), **keskin ağız / nüfuz eden uç** (`root_000002/B005`): Bu dal kılıçla sınırlı değildir; bıçak, mızrak, dil, bakış ve anlayışın keskinliği veya etkisi gibi taşıyıcılara yayılır. `السُّرَاط` (es-sürâṭ) doğrudan belirli nitelikteki kılıç adıdır.
    - `جُمَاد` (cumâd), **sert ve kesici kılıç** (`root_000258/B009`): Bu dal kılıcı `صارم قاطع` (ṣârim ḳâṭıʿ), sert ve kesici oluşuyla niteler. `السُّرَاط` (es-sürâṭ) ise aynı kesicilik alanında darbede geçiş imgesini ayrıca taşır.

    ## Kur'an oluşum gözlemevi

    Bu bölüm yalnız gözlenebilir biçim, morfoloji, dilbilgisi ve bağlantıları verir. Hiçbir kullanım B001, B002 veya B003'e atanmaz.

    ### Mekanik özet

    - 45 köklü morfem, 45 kelime ve 45 ayet vardır; tamamı `صِرَاط` (ṣirâṭ) lemmalı isimdir.
    - Gözlenen bağlantılar; sıfat, edat tamamlayıcısı, doğrudan nesne, izafet, yüklemleme, hâl, yer zarfı ve bedel/açıklayıcı ilişki gruplarına ayrılır.
    - Bu sayımlar çeviri hükmü veya dal etkinleştirmesi değildir.
    """
)


RELATION_TR = {
    "adjective": "sıfat",
    "adverbial": "zarf",
    "apposition": "bedel/açıklayıcı",
    "circumstantial": "hâl",
    "direct_object": "doğrudan nesne",
    "idafa": "izafet",
    "predication": "yüklemleme",
    "prep_complement": "edat tamamlayıcısı",
}

CASE_TR = {"ACC": "mansup", "GEN": "mecrur", "NOM": "merfu"}


def morphology_tr(occurrence: dict[str, str], surface: str) -> str:
    tokens = occurrence["morph_features"].split("|")
    parts = ["isim", "eril"]
    if "INDEF" in tokens:
        parts.append("belirsiz")
    for token, label in CASE_TR.items():
        if token in tokens:
            parts.append(label)
            break

    if surface.endswith(("ي", "ى")):
        parts.append("1. tekil kişi iyelik eki")
    elif surface.endswith("كَ"):
        parts.append("2. tekil kişi iyelik eki")
    return ", ".join(parts)


def attachment_tr(row: dict[str, str]) -> str:
    relation = RELATION_TR.get(row["relation"], row["relation"])
    confidence = {"high": "yüksek", "medium": "orta", "low": "düşük"}.get(
        row.get("confidence", ""), row.get("confidence", "")
    )
    root_is_dependent = row.get("dep_root_norm") == "ص ر ط"
    other = row.get("head_surface") if root_is_dependent else row.get("dep_surface")
    prep = row.get("prep_base", "")
    if row["relation"] == "prep_complement":
        if root_is_dependent and prep == other:
            detail = prep
        elif root_is_dependent and prep and other:
            detail = f"{prep}; yönetici: {other}"
        elif prep and other:
            detail = f"{prep} + {other}"
        elif prep and row.get("dep_part") == "pronoun_suffix":
            detail = f"{prep} + zamir eki"
        else:
            detail = prep or other or "ayrıntısız bağlantı"
    else:
        detail = other or "ayrıntısız bağlantı"
    return f"{relation}: {detail} ({confidence})"


def render() -> str:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    occurrences = packet["qac"]["occurrences"]
    word_surfaces = {
        word["qac_word_ref"]: word["surface_ar"]
        for ayah in packet["qac"]["ayah_contexts"]
        for word in ayah["words"]
    }
    attachments: dict[tuple[int, int], list[dict[str, str]]] = {}
    for row in packet["attachments"]["attachments"]:
        if row.get("dep_root_norm") != "ص ر ط" and row.get("head_root_norm") != "ص ر ط":
            continue
        key = (int(row["sura"]), int(row["ayah"]))
        attachments.setdefault(key, []).append(row)

    relation_counts = Counter(
        row["relation"]
        for rows in attachments.values()
        for row in rows
    )
    modifier_rows = [
        row
        for rows in attachments.values()
        for row in rows
        if row.get("head_root_norm") == "ص ر ط"
        and row["relation"] in {"adjective", "circumstantial"}
    ]
    mustaqim_rows = [row for row in modifier_rows if row.get("dep_root_norm") == "ق و م"]
    sawiyy_rows = [row for row in modifier_rows if row.get("dep_root_norm") != "ق و م"]
    mustaqim_refs = {(int(row["sura"]), int(row["ayah"])) for row in mustaqim_rows}
    sawiyy_refs = {(int(row["sura"]), int(row["ayah"])) for row in sawiyy_rows}
    all_refs = {(int(row["surah"]), int(row["ayah"])) for row in occurrences}
    unqualified_refs = sorted(all_refs - mustaqim_refs - sawiyy_refs)
    case_counts = Counter()
    form_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for occurrence in occurrences:
        key = (
            occurrence["lemma_ar"],
            occurrence["surface_ar"],
            occurrence["pos"],
            occurrence["morph_features"],
        )
        form_groups.setdefault(key, []).append(occurrence)

    form_summary = [
        "### Oluşumların biçime göre düzeni",
        "",
        "Biçim grubu, QAC'nin tam `(lemma, kök yüzeyi, sözcük türü, morfolojik özellikler)` anahtarıyla belirlenir. Gruplar ilk Kur'an oluşumunun sırasını, her grubun içindeki satırlar da Kur'an sırasını izler.",
        "",
        "| Biçim | Lemma | Kök yüzeyi | Morfoloji | Oluşum |",
        "|---|---|---|---|---:|",
    ]
    form_tables: list[str] = []
    for ordinal, ((lemma, root_surface, _pos, _features), rows) in enumerate(
        form_groups.items(), start=1
    ):
        form_id = f"F{ordinal:03d}"
        form_morphology = morphology_tr(rows[0], root_surface)
        form_summary.append(
            f"| `{form_id}` | `{lemma}` | `{root_surface}` | {form_morphology} | {len(rows)} |"
        )
        occurrence_table = [
            f"#### {form_id}: `{root_surface}`",
            "",
            "| QAC konumu | Ayet içindeki yüzey | Oluşum morfolojisi | Sözdizimsel bağlantılar |",
            "|---|---|---|---|",
        ]
        for occurrence in rows:
            key = (int(occurrence["surah"]), int(occurrence["ayah"]))
            surface = word_surfaces[occurrence["qac_word_ref"]]
            morphology = morphology_tr(occurrence, surface)
            case_counts.update(label for label in CASE_TR.values() if label in morphology)
            linked = "; ".join(attachment_tr(row) for row in attachments.get(key, []))
            occurrence_table.append(
                f"| `{occurrence['qac_ref']}` | `{surface}` | {morphology} | {linked or 'Bağlantı kaydı yok'} |"
            )
        form_tables.append("\n".join(occurrence_table))

    counts = ", ".join(
        f"{RELATION_TR.get(relation, relation)}: {count}"
        for relation, count in sorted(relation_counts.items())
    )
    cases = ", ".join(f"{case}: {count}" for case, count in sorted(case_counts.items()))
    mustaqim_relations = Counter(row["relation"] for row in mustaqim_rows)
    unqualified = ", ".join(f"{sura}:{ayah}" for sura, ayah in unqualified_refs)
    appendix = dedent(
        f"""

        ### Toplu mekanik sayımlar

        - İrab dağılımı: {cases}.
        - Bağlantı satırları: {counts}.

        ### Niteleyici örüntüsü

        - `مُسْتَقِيم` (müstaḳîm), 45 oluşumun {len(mustaqim_refs)} tanesinde `صِرَاط` (ṣirâṭ) ile bağlantılıdır: {mustaqim_relations['adjective']} sıfat ve {mustaqim_relations['circumstantial']} hâl bağlantısı. Hâl bağlantıları `6:126` ve `6:153` ayetlerindedir.
        - `سَوِيّ` (seviyy), {len(sawiyy_refs)} oluşumda sıfat bağlantısı taşır: `19:43` ve `20:135`.
        - Bu iki niteleyiciden hiçbirini taşımayan {len(unqualified_refs)} oluşum vardır: `{unqualified}`.
        - Dolayısıyla “ṣirâṭ Kur'an'da her zaman müstaḳîm ile gelir” denemez. Bu sonuç dal veya anlam tayini değil, bağlantı satırlarının mekanik özetidir.

        ## Çevirmen ajan için dikkat notu örneği

        `6:153` ayetinde `صِرَاطِي` (ṣirâṭî), “benim ṣirâṭım”, yüklemleme içinde kullanılır; `مُسْتَقِيمًا` (müstaḳîmen) ona hâl ilişkisiyle bağlanır ve ardından `فَاتَّبِعُوهُ` (fe'ttebiʿûhü), “ona uyun”, gelir. Aynı ayette `السُّبُل` (es-sübül) ve `سَبِيلِهِ` (sebîlihî) biçimleri de bulunur. Türkçede bunların tamamını düşünmeden “yol” yapmak, ayette gözle görülen farklı Arapça söz seçimini düzleştirebilir; çevirmen ajan bu kaybı koruma, telafi etme veya gerekçeli olarak kabul etme seçeneklerini tartışmalıdır. Bu not herhangi bir oluşumu bir dala atamaz.

        ## Kanıt ve bağlantı notu

        - Dal kimlikleri, Arapça sınırlar, sözlük kaynakları, QAC konumları ve bağlantılar `root_000858` paketinden gelir.
        - QNet yalnız komşu adayı bulur. Yayınlanan her Arapça komşu ayrımı, parantez içindeki `(root_id/branch_id)` hedefine ve o hedefin sözlük kanıtına bağlanmalıdır.
        - Bu örnekte `سَبِيل` (sebîl) ve `طَرِيق` (ṭarîḳ) karşılaştırmaları V4 dal sınırlarının karşılaştırmalı okumasıdır; üretim maddesinde kabul edilmiş Furûḳ iddiası ve kanıt tutamaklarıyla desteklenmelidir.
        """
    )
    generated_occurrences = "\n".join(form_summary) + "\n\n" + "\n\n".join(form_tables)
    return EDITORIAL + "\n" + generated_occurrences + appendix


if __name__ == "__main__":
    OUTPUT_PATH.write_text(render(), encoding="utf-8")
    print(OUTPUT_PATH)
