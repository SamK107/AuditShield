# Structure Hiérarchique du Projet AUDITSHIELD
**Généré le:** 2025-11-03 21:47:02
---

```
auditshield/
├── assets
│   └── Kit_Complet_Preparation_Couverture_BSG.docx
├── config
│   ├── settings
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
├── core
│   ├── templates
│   │   └── core
│   │       ├── about.html
│   │       ├── cgv.html
│   │       ├── contact.html
│   │       ├── home.html
│   │       ├── landing_comingsoon.html
│   │       └── policy.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── views_debug.py
├── docs
│   ├── CINETPAY.md
│   ├── DEPLOY.md
│   ├── EXPLICATION_CONFIG_CINETPAY.md
│   ├── GO_LIVE_CINETPAY.md
│   ├── PAYMENT_CINETPAY.md
│   └── RECETTE_CINETPAY.md
├── downloads
│   ├── management
│   │   ├── commands
│   │   │   ├── __init__.py
│   │   │   ├── check_receipt.py
│   │   │   ├── create_entitlement.py
│   │   │   ├── fetch_receipts.py
│   │   │   └── import_external_orders.py
│   │   └── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_downloadcategory_remove_assetevent_asset_and_more.py
│   │   ├── 0003_add_category_protection.py
│   │   ├── 0004_alter_downloadcategory_required_sku_purchaseclaim_and_more.py
│   │   ├── 0005_remove_downloadcategory_is_protected_and_more.py
│   │   ├── 0006_downloadcategory_is_protected_and_more.py
│   │   ├── 0007_secure_categories_phase1.py
│   │   ├── 0008_secure_phase1_slugs.py
│   │   ├── 0009_externalentitlement.py
│   │   ├── 0010_remove_selar_platform.py
│   │   └── __init__.py
│   ├── templates
│   │   └── downloads
│   │       ├── _asset_grid.html
│   │       ├── _download_button.html
│   │       ├── asset_upload.html
│   │       ├── asset_upload_success.html
│   │       ├── category_page.html
│   │       ├── claim_access.html
│   │       ├── kit_preparation_start.html
│   │       ├── kit_preparation_thanks.html
│   │       ├── manual_claim.html
│   │       ├── secure.html
│   │       └── secure_downloads.html
│   ├── tests
│   │   ├── conftest.py
│   │   ├── test_admin_upload.py
│   │   ├── test_admin_upload_signal_safe.py
│   │   ├── test_bonus_gate_sku_only.py
│   │   ├── test_downloads_gate_namespace.py
│   │   ├── test_gating.py
│   │   ├── test_phase1_gate.py
│   │   └── test_phase1_gate_bonus.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── public_urls.py
│   ├── services.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── views_manual_claim.py
├── legal
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_seed_legal_pages.py
│   │   └── __init__.py
│   ├── templates
│   │   └── legal
│   │       ├── _mentions_modal.html
│   │       └── legal_page.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── logs
│   ├── app.log
│   └── fetch_receipts.log
├── media
│   ├── deliverables
│   │   ├── 6x9
│   │   │   ├── Audit_Sans_Peur_PDF6X9.pdf
│   │   │   └── Audit_Sans_Peur_PDF6X9_bO1ybkC.pdf
│   │   └── a4
│   │       ├── Audit_Sans_Peur_PDFA4.pdf
│   │       └── Audit_Sans_Peur_PDFA4_4UFKOzs.pdf
│   └── downloads
│       └── 2025
│           ├── 09
│           │   ├── Audit_Sans_Peur_PDFA4.pdf
│           │   ├── Audit_Sans_Peur_PDFA4_9PDmFZk.pdf
│           │   ├── Checklist_Audit_Collectivites.xlsx
│           │   ├── Checklist_Audit_Collectivites_8IB3rpX.xlsx
│           │   ├── Checklist_Audit_Projets.xlsx
│           │   ├── Checklist_Audit_Projets_yIGpj5c.xlsx
│           │   └── Checklist_Audit_Structures_Publiques.xlsx
│           └── 10
│               ├── Audit_Sans_Peur_PDF6X9.pdf
│               ├── Audit_Sans_Peur_PDF6X9_Z7z8OV9.pdf
│               ├── Comptabilite_Matieres_Irregularites.pdf
│               ├── DFM_Irregularites.pdf
│               └── EPIC_Irregularites.pdf
├── private_media
│   └── downloads
│       └── 2025
│           └── 10
│               ├── bonus_reponses.txt
│               ├── bonus_reponses_fT0e6Fk.txt
│               ├── checklist_projets.csv
│               ├── checklist_projets_MR9wMmo.csv
│               ├── checklist_publiques.txt
│               ├── checklist_publiques_3gNdiba.txt
│               ├── irregs.csv
│               ├── irregs_3299M6y.csv
│               ├── plan_action.txt
│               ├── plan_action_F6oTs54.txt
│               └── responding-to-audit-findings-montgomery-college.pdf
├── scripts
│   ├── enrich_buy_links.sh
│   ├── recipe_cinetpay_local.ps1
│   └── recipe_cinetpay_local.sh
├── static
│   ├── admin
│   │   ├── css
│   │   │   ├── vendor
│   │   │   │   └── select2
│   │   │   │       ├── LICENSE-SELECT2.f94142512c91.md
│   │   │   │       ├── LICENSE-SELECT2.md
│   │   │   │       ├── select2.a2194c262648.css
│   │   │   │       ├── select2.css
│   │   │   │       ├── select2.min.9f54e6414f87.css
│   │   │   │       ├── select2.min.css
│   │   │   ├── autocomplete.4a81fc4242d0.css
│   │   │   ├── autocomplete.css
│   │   │   ├── base.523eb49842a7.css
│   │   │   ├── base.css
│   │   │   ├── changelists.9237a1ac391b.css
│   │   │   ├── changelists.css
│   │   │   ├── dark_mode.css
│   │   │   ├── dark_mode.ef27a31af300.css
│   │   │   ├── dashboard.css
│   │   │   ├── dashboard.e90f2068217b.css
│   │   │   ├── forms.c14e1cb06392.css
│   │   │   ├── forms.css
│   │   │   ├── login.586129c60a93.css
│   │   │   ├── login.css
│   │   │   ├── nav_sidebar.269a1bd44627.css
│   │   │   ├── nav_sidebar.css
│   │   │   ├── responsive.css
│   │   │   ├── responsive.f6533dab034d.css
│   │   │   ├── responsive_rtl.7d1130848605.css
│   │   │   ├── responsive_rtl.css
│   │   │   ├── rtl.512d4b53fc59.css
│   │   │   ├── rtl.css
│   │   │   ├── widgets.css
│   │   │   ├── widgets.ee33ab26c7c2.css
│   │   ├── img
│   │   │   ├── gis
│   │   │   │   ├── move_vertex_off.7a23bf31ef8a.svg
│   │   │   │   ├── move_vertex_off.svg
│   │   │   │   ├── move_vertex_on.0047eba25b67.svg
│   │   │   │   ├── move_vertex_on.svg
│   │   │   ├── calendar-icons.39b290681a8b.svg
│   │   │   ├── calendar-icons.svg
│   │   │   ├── icon-addlink.d519b3bab011.svg
│   │   │   ├── icon-addlink.svg
│   │   │   ├── icon-alert.034cc7d8a67f.svg
│   │   │   ├── icon-alert.svg
│   │   │   ├── icon-calendar.ac7aea671bea.svg
│   │   │   ├── icon-calendar.svg
│   │   │   ├── icon-changelink.18d2fd706348.svg
│   │   │   ├── icon-changelink.svg
│   │   │   ├── icon-clock.e1d4dfac3f2b.svg
│   │   │   ├── icon-clock.svg
│   │   │   ├── icon-deletelink.564ef9dc3854.svg
│   │   │   ├── icon-deletelink.svg
│   │   │   ├── icon-no.439e821418cd.svg
│   │   │   ├── icon-no.svg
│   │   │   ├── icon-unknown-alt.81536e128bb6.svg
│   │   │   ├── icon-unknown-alt.svg
│   │   │   ├── icon-unknown.a18cb4398978.svg
│   │   │   ├── icon-unknown.svg
│   │   │   ├── icon-viewlink.41eb31f7826e.svg
│   │   │   ├── icon-viewlink.svg
│   │   │   ├── icon-yes.d2f9f035226a.svg
│   │   │   ├── icon-yes.svg
│   │   │   ├── inline-delete.fec1b761f254.svg
│   │   │   ├── inline-delete.svg
│   │   │   ├── LICENSE
│   │   │   ├── LICENSE.2c54f4e1ca1c
│   │   │   ├── README.a70711a38d87.txt
│   │   │   ├── README.txt
│   │   │   ├── search.7cf54ff789c6.svg
│   │   │   ├── search.svg
│   │   │   ├── selector-icons.b4555096cea2.svg
│   │   │   ├── selector-icons.svg
│   │   │   ├── sorting-icons.3a097b59f104.svg
│   │   │   ├── sorting-icons.svg
│   │   │   ├── tooltag-add.e59d620a9742.svg
│   │   │   ├── tooltag-add.svg
│   │   │   ├── tooltag-arrowright.bbfb788a849e.svg
│   │   │   ├── tooltag-arrowright.svg
│   │   └── js
│   │       ├── admin
│   │       │   ├── DateTimeShortcuts.9f6e209cebca.js
│   │       │   ├── DateTimeShortcuts.js
│   │       │   ├── RelatedObjectLookups.8609f99b9ab2.js
│   │       │   ├── RelatedObjectLookups.js
│   │       ├── vendor
│   │       │   ├── jquery
│   │       │   │   ├── jquery.0208b96062ba.js
│   │       │   │   ├── jquery.js
│   │       │   │   ├── jquery.min.641dd1437010.js
│   │       │   │   ├── jquery.min.js
│   │       │   │   ├── LICENSE.de877aa6d744.txt
│   │       │   │   ├── LICENSE.txt
│   │       │   ├── select2
│   │       │   │   ├── i18n
│   │       │   │   │   ├── af.4f6fcd73488c.js
│   │       │   │   │   ├── af.js
│   │       │   │   │   ├── ar.65aa8e36bf5d.js
│   │       │   │   │   ├── ar.js
│   │       │   │   │   ├── az.270c257daf81.js
│   │       │   │   │   ├── az.js
│   │       │   │   │   ├── bg.39b8be30d4f0.js
│   │       │   │   │   ├── bg.js
│   │       │   │   │   ├── bn.6d42b4dd5665.js
│   │       │   │   │   ├── bn.js
│   │       │   │   │   ├── bs.91624382358e.js
│   │       │   │   │   ├── bs.js
│   │       │   │   │   ├── ca.a166b745933a.js
│   │       │   │   │   ├── ca.js
│   │       │   │   │   ├── cs.4f43e8e7d33a.js
│   │       │   │   │   ├── cs.js
│   │       │   │   │   ├── da.766346afe4dd.js
│   │       │   │   │   ├── da.js
│   │       │   │   │   ├── de.8a1c222b0204.js
│   │       │   │   │   ├── de.js
│   │       │   │   │   ├── dsb.56372c92d2f1.js
│   │       │   │   │   ├── dsb.js
│   │       │   │   │   ├── el.27097f071856.js
│   │       │   │   │   ├── el.js
│   │       │   │   │   ├── en.cf932ba09a98.js
│   │       │   │   │   ├── en.js
│   │       │   │   │   ├── es.66dbc2652fb1.js
│   │       │   │   │   ├── es.js
│   │       │   │   │   ├── et.2b96fd98289d.js
│   │       │   │   │   ├── et.js
│   │       │   │   │   ├── eu.adfe5c97b72c.js
│   │       │   │   │   ├── eu.js
│   │       │   │   │   ├── fa.3b5bd1961cfd.js
│   │       │   │   │   ├── fa.js
│   │       │   │   │   ├── fi.614ec42aa9ba.js
│   │       │   │   │   ├── fi.js
│   │       │   │   │   ├── fr.05e0542fcfe6.js
│   │       │   │   │   ├── fr.js
│   │       │   │   │   ├── gl.d99b1fedaa86.js
│   │       │   │   │   ├── gl.js
│   │       │   │   │   ├── he.e420ff6cd3ed.js
│   │       │   │   │   ├── he.js
│   │       │   │   │   ├── hi.70640d41628f.js
│   │       │   │   │   ├── hi.js
│   │       │   │   │   ├── hr.a2b092cc1147.js
│   │       │   │   │   ├── hr.js
│   │       │   │   │   ├── hsb.fa3b55265efe.js
│   │       │   │   │   ├── hsb.js
│   │       │   │   │   ├── hu.6ec6039cb8a3.js
│   │       │   │   │   ├── hu.js
│   │       │   │   │   ├── hy.c7babaeef5a6.js
│   │       │   │   │   ├── hy.js
│   │       │   │   │   ├── id.04debded514d.js
│   │       │   │   │   ├── id.js
│   │       │   │   │   ├── is.3ddd9a6a97e9.js
│   │       │   │   │   ├── is.js
│   │       │   │   │   ├── it.be4fe8d365b5.js
│   │       │   │   │   ├── it.js
│   │       │   │   │   ├── ja.170ae885d74f.js
│   │       │   │   │   ├── ja.js
│   │       │   │   │   ├── ka.2083264a54f0.js
│   │       │   │   │   ├── ka.js
│   │       │   │   │   ├── km.c23089cb06ca.js
│   │       │   │   │   ├── km.js
│   │       │   │   │   ├── ko.e7be6c20e673.js
│   │       │   │   │   ├── ko.js
│   │       │   │   │   ├── lt.23c7ce903300.js
│   │       │   │   │   ├── lt.js
│   │       │   │   │   ├── lv.08e62128eac1.js
│   │       │   │   │   ├── lv.js
│   │       │   │   │   ├── mk.dabbb9087130.js
│   │       │   │   │   ├── mk.js
│   │       │   │   │   ├── ms.4ba82c9a51ce.js
│   │       │   │   │   ├── ms.js
│   │       │   │   │   ├── nb.da2fce143f27.js
│   │       │   │   │   ├── nb.js
│   │       │   │   │   ├── ne.3d79fd3f08db.js
│   │       │   │   │   ├── ne.js
│   │       │   │   │   ├── nl.997868a37ed8.js
│   │       │   │   │   ├── nl.js
│   │       │   │   │   ├── pl.6031b4f16452.js
│   │       │   │   │   ├── pl.js
│   │       │   │   │   ├── ps.38dfa47af9e0.js
│   │       │   │   │   ├── ps.js
│   │       │   │   │   ├── pt-BR.e1b294433e7f.js
│   │       │   │   │   ├── pt-BR.js
│   │       │   │   │   ├── pt.33b4a3b44d43.js
│   │       │   │   │   ├── pt.js
│   │       │   │   │   ├── ro.f75cb460ec3b.js
│   │       │   │   │   ├── ro.js
│   │       │   │   │   ├── ru.934aa95f5b5f.js
│   │       │   │   │   ├── ru.js
│   │       │   │   │   ├── sk.33d02cef8d11.js
│   │       │   │   │   ├── sk.js
│   │       │   │   │   ├── sl.131a78bc0752.js
│   │       │   │   │   ├── sl.js
│   │       │   │   │   ├── sq.5636b60d29c9.js
│   │       │   │   │   ├── sq.js
│   │       │   │   │   ├── sr-Cyrl.f254bb8c4c7c.js
│   │       │   │   │   ├── sr-Cyrl.js
│   │       │   │   │   ├── sr.5ed85a48f483.js
│   │       │   │   │   ├── sr.js
│   │       │   │   │   ├── sv.7a9c2f71e777.js
│   │       │   │   │   ├── sv.js
│   │       │   │   │   ├── th.f38c20b0221b.js
│   │       │   │   │   ├── th.js
│   │       │   │   │   ├── tk.7c572a68c78f.js
│   │       │   │   │   ├── tk.js
│   │       │   │   │   ├── tr.b5a0643d1545.js
│   │       │   │   │   ├── tr.js
│   │       │   │   │   ├── uk.8cede7f4803c.js
│   │       │   │   │   ├── uk.js
│   │       │   │   │   ├── vi.097a5b75b3e1.js
│   │       │   │   │   ├── vi.js
│   │       │   │   │   ├── zh-CN.2cff662ec5f9.js
│   │       │   │   │   ├── zh-CN.js
│   │       │   │   │   ├── zh-TW.04554a227c2b.js
│   │       │   │   │   ├── zh-TW.js
│   │       │   │   ├── LICENSE.f94142512c91.md
│   │       │   │   ├── LICENSE.md
│   │       │   │   ├── select2.full.c2afdeda3058.js
│   │       │   │   ├── select2.full.js
│   │       │   │   ├── select2.full.min.fcd7500d8e13.js
│   │       │   │   ├── select2.full.min.js
│   │       │   └── xregexp
│   │       │       ├── LICENSE.bf79e414957a.txt
│   │       │       ├── LICENSE.txt
│   │       │       ├── xregexp.efda034b9537.js
│   │       │       ├── xregexp.js
│   │       │       ├── xregexp.min.b0439563a5d3.js
│   │       │       ├── xregexp.min.js
│   │       ├── actions.eac7e3441574.js
│   │       ├── actions.js
│   │       ├── autocomplete.01591ab27be7.js
│   │       ├── autocomplete.js
│   │       ├── calendar.f8a5d055eb33.js
│   │       ├── calendar.js
│   │       ├── cancel.ecc4c5ca7b32.js
│   │       ├── cancel.js
│   │       ├── change_form.9d8ca4f96b75.js
│   │       ├── change_form.js
│   │       ├── collapse.f84e7410290f.js
│   │       ├── collapse.js
│   │       ├── core.cf103cd04ebf.js
│   │       ├── core.js
│   │       ├── filters.0e360b7a9f80.js
│   │       ├── filters.js
│   │       ├── inlines.22d4d93c00b4.js
│   │       ├── inlines.js
│   │       ├── jquery.init.b7781a0897fc.js
│   │       ├── jquery.init.js
│   │       ├── nav_sidebar.3b9190d420b1.js
│   │       ├── nav_sidebar.js
│   │       ├── popup_response.c6cc78ea5551.js
│   │       ├── popup_response.js
│   │       ├── prepopulate.bd2361dfd64d.js
│   │       ├── prepopulate.js
│   │       ├── prepopulate_init.6cac7f3105b8.js
│   │       ├── prepopulate_init.js
│   │       ├── SelectBox.7d3ce5a98007.js
│   │       ├── SelectBox.js
│   │       ├── SelectFilter2.bdb8d0cc579e.js
│   │       ├── SelectFilter2.js
│   │       ├── theme.ab270f56bb9c.js
│   │       ├── theme.js
│   │       ├── urlify.ae970a820212.js
│   │       ├── urlify.js
│   ├── brand
│   │   ├── ebook_carousel
│   │   │   ├── chap_1.jpg
│   │   │   ├── chap_10.jpg
│   │   │   ├── chap_9.jpg
│   │   │   ├── cover.jpg
│   │   │   └── Question_1.jpg
│   │   ├── audit-sans-peur-cover.svg
│   │   ├── logo_img2.svg
│   │   ├── logo_img2_optimized.ico
│   │   ├── logo_img2_optimized_16.png
│   │   ├── logo_img2_optimized_180.png
│   │   ├── logo_img2_optimized_32.png
│   │   ├── logo_img2_optimized_48.png
│   │   ├── logo_img2_optimized_512.png
│   │   ├── logo_img2_optimized_64.png
│   │   └── tmp_large.png
│   ├── css
│   │   ├── files
│   │   │   ├── inter-cyrillic-100-italic.woff
│   │   │   ├── inter-cyrillic-100-italic.woff2
│   │   │   ├── inter-cyrillic-100-normal.woff
│   │   │   ├── inter-cyrillic-100-normal.woff2
│   │   │   ├── inter-cyrillic-200-italic.woff
│   │   │   ├── inter-cyrillic-200-italic.woff2
│   │   │   ├── inter-cyrillic-200-normal.woff
│   │   │   ├── inter-cyrillic-200-normal.woff2
│   │   │   ├── inter-cyrillic-300-italic.woff
│   │   │   ├── inter-cyrillic-300-italic.woff2
│   │   │   ├── inter-cyrillic-300-normal.woff
│   │   │   ├── inter-cyrillic-300-normal.woff2
│   │   │   ├── inter-cyrillic-400-italic.woff
│   │   │   ├── inter-cyrillic-400-italic.woff2
│   │   │   ├── inter-cyrillic-400-normal.woff
│   │   │   ├── inter-cyrillic-400-normal.woff2
│   │   │   ├── inter-cyrillic-500-italic.woff
│   │   │   ├── inter-cyrillic-500-italic.woff2
│   │   │   ├── inter-cyrillic-500-normal.woff
│   │   │   ├── inter-cyrillic-500-normal.woff2
│   │   │   ├── inter-cyrillic-600-italic.woff
│   │   │   ├── inter-cyrillic-600-italic.woff2
│   │   │   ├── inter-cyrillic-600-normal.woff
│   │   │   ├── inter-cyrillic-600-normal.woff2
│   │   │   ├── inter-cyrillic-700-italic.woff
│   │   │   ├── inter-cyrillic-700-italic.woff2
│   │   │   ├── inter-cyrillic-700-normal.woff
│   │   │   ├── inter-cyrillic-700-normal.woff2
│   │   │   ├── inter-cyrillic-800-italic.woff
│   │   │   ├── inter-cyrillic-800-italic.woff2
│   │   │   ├── inter-cyrillic-800-normal.woff
│   │   │   ├── inter-cyrillic-800-normal.woff2
│   │   │   ├── inter-cyrillic-900-italic.woff
│   │   │   ├── inter-cyrillic-900-italic.woff2
│   │   │   ├── inter-cyrillic-900-normal.woff
│   │   │   ├── inter-cyrillic-900-normal.woff2
│   │   │   ├── inter-cyrillic-ext-100-italic.woff
│   │   │   ├── inter-cyrillic-ext-100-italic.woff2
│   │   │   ├── inter-cyrillic-ext-100-normal.woff
│   │   │   ├── inter-cyrillic-ext-100-normal.woff2
│   │   │   ├── inter-cyrillic-ext-200-italic.woff
│   │   │   ├── inter-cyrillic-ext-200-italic.woff2
│   │   │   ├── inter-cyrillic-ext-200-normal.woff
│   │   │   ├── inter-cyrillic-ext-200-normal.woff2
│   │   │   ├── inter-cyrillic-ext-300-italic.woff
│   │   │   ├── inter-cyrillic-ext-300-italic.woff2
│   │   │   ├── inter-cyrillic-ext-300-normal.woff
│   │   │   ├── inter-cyrillic-ext-300-normal.woff2
│   │   │   ├── inter-cyrillic-ext-400-italic.woff
│   │   │   ├── inter-cyrillic-ext-400-italic.woff2
│   │   │   ├── inter-cyrillic-ext-400-normal.woff
│   │   │   ├── inter-cyrillic-ext-400-normal.woff2
│   │   │   ├── inter-cyrillic-ext-500-italic.woff
│   │   │   ├── inter-cyrillic-ext-500-italic.woff2
│   │   │   ├── inter-cyrillic-ext-500-normal.woff
│   │   │   ├── inter-cyrillic-ext-500-normal.woff2
│   │   │   ├── inter-cyrillic-ext-600-italic.woff
│   │   │   ├── inter-cyrillic-ext-600-italic.woff2
│   │   │   ├── inter-cyrillic-ext-600-normal.woff
│   │   │   ├── inter-cyrillic-ext-600-normal.woff2
│   │   │   ├── inter-cyrillic-ext-700-italic.woff
│   │   │   ├── inter-cyrillic-ext-700-italic.woff2
│   │   │   ├── inter-cyrillic-ext-700-normal.woff
│   │   │   ├── inter-cyrillic-ext-700-normal.woff2
│   │   │   ├── inter-cyrillic-ext-800-italic.woff
│   │   │   ├── inter-cyrillic-ext-800-italic.woff2
│   │   │   ├── inter-cyrillic-ext-800-normal.woff
│   │   │   ├── inter-cyrillic-ext-800-normal.woff2
│   │   │   ├── inter-cyrillic-ext-900-italic.woff
│   │   │   ├── inter-cyrillic-ext-900-italic.woff2
│   │   │   ├── inter-cyrillic-ext-900-normal.woff
│   │   │   ├── inter-cyrillic-ext-900-normal.woff2
│   │   │   ├── inter-greek-100-italic.woff
│   │   │   ├── inter-greek-100-italic.woff2
│   │   │   ├── inter-greek-100-normal.woff
│   │   │   ├── inter-greek-100-normal.woff2
│   │   │   ├── inter-greek-200-italic.woff
│   │   │   ├── inter-greek-200-italic.woff2
│   │   │   ├── inter-greek-200-normal.woff
│   │   │   ├── inter-greek-200-normal.woff2
│   │   │   ├── inter-greek-300-italic.woff
│   │   │   ├── inter-greek-300-italic.woff2
│   │   │   ├── inter-greek-300-normal.woff
│   │   │   ├── inter-greek-300-normal.woff2
│   │   │   ├── inter-greek-400-italic.woff
│   │   │   ├── inter-greek-400-italic.woff2
│   │   │   ├── inter-greek-400-normal.woff
│   │   │   ├── inter-greek-400-normal.woff2
│   │   │   ├── inter-greek-500-italic.woff
│   │   │   ├── inter-greek-500-italic.woff2
│   │   │   ├── inter-greek-500-normal.woff
│   │   │   ├── inter-greek-500-normal.woff2
│   │   │   ├── inter-greek-600-italic.woff
│   │   │   ├── inter-greek-600-italic.woff2
│   │   │   ├── inter-greek-600-normal.woff
│   │   │   ├── inter-greek-600-normal.woff2
│   │   │   ├── inter-greek-700-italic.woff
│   │   │   ├── inter-greek-700-italic.woff2
│   │   │   ├── inter-greek-700-normal.woff
│   │   │   ├── inter-greek-700-normal.woff2
│   │   │   ├── inter-greek-800-italic.woff
│   │   │   ├── inter-greek-800-italic.woff2
│   │   │   ├── inter-greek-800-normal.woff
│   │   │   ├── inter-greek-800-normal.woff2
│   │   │   ├── inter-greek-900-italic.woff
│   │   │   ├── inter-greek-900-italic.woff2
│   │   │   ├── inter-greek-900-normal.woff
│   │   │   ├── inter-greek-900-normal.woff2
│   │   │   ├── inter-greek-ext-100-italic.woff
│   │   │   ├── inter-greek-ext-100-italic.woff2
│   │   │   ├── inter-greek-ext-100-normal.woff
│   │   │   ├── inter-greek-ext-100-normal.woff2
│   │   │   ├── inter-greek-ext-200-italic.woff
│   │   │   ├── inter-greek-ext-200-italic.woff2
│   │   │   ├── inter-greek-ext-200-normal.woff
│   │   │   ├── inter-greek-ext-200-normal.woff2
│   │   │   ├── inter-greek-ext-300-italic.woff
│   │   │   ├── inter-greek-ext-300-italic.woff2
│   │   │   ├── inter-greek-ext-300-normal.woff
│   │   │   ├── inter-greek-ext-300-normal.woff2
│   │   │   ├── inter-greek-ext-400-italic.woff
│   │   │   ├── inter-greek-ext-400-italic.woff2
│   │   │   ├── inter-greek-ext-400-normal.woff
│   │   │   ├── inter-greek-ext-400-normal.woff2
│   │   │   ├── inter-greek-ext-500-italic.woff
│   │   │   ├── inter-greek-ext-500-italic.woff2
│   │   │   ├── inter-greek-ext-500-normal.woff
│   │   │   ├── inter-greek-ext-500-normal.woff2
│   │   │   ├── inter-greek-ext-600-italic.woff
│   │   │   ├── inter-greek-ext-600-italic.woff2
│   │   │   ├── inter-greek-ext-600-normal.woff
│   │   │   ├── inter-greek-ext-600-normal.woff2
│   │   │   ├── inter-greek-ext-700-italic.woff
│   │   │   ├── inter-greek-ext-700-italic.woff2
│   │   │   ├── inter-greek-ext-700-normal.woff
│   │   │   ├── inter-greek-ext-700-normal.woff2
│   │   │   ├── inter-greek-ext-800-italic.woff
│   │   │   ├── inter-greek-ext-800-italic.woff2
│   │   │   ├── inter-greek-ext-800-normal.woff
│   │   │   ├── inter-greek-ext-800-normal.woff2
│   │   │   ├── inter-greek-ext-900-italic.woff
│   │   │   ├── inter-greek-ext-900-italic.woff2
│   │   │   ├── inter-greek-ext-900-normal.woff
│   │   │   ├── inter-greek-ext-900-normal.woff2
│   │   │   ├── inter-latin-100-italic.woff
│   │   │   ├── inter-latin-100-italic.woff2
│   │   │   ├── inter-latin-100-normal.woff
│   │   │   ├── inter-latin-100-normal.woff2
│   │   │   ├── inter-latin-200-italic.woff
│   │   │   ├── inter-latin-200-italic.woff2
│   │   │   ├── inter-latin-200-normal.woff
│   │   │   ├── inter-latin-200-normal.woff2
│   │   │   ├── inter-latin-300-italic.woff
│   │   │   ├── inter-latin-300-italic.woff2
│   │   │   ├── inter-latin-300-normal.woff
│   │   │   ├── inter-latin-300-normal.woff2
│   │   │   ├── inter-latin-400-italic.woff
│   │   │   ├── inter-latin-400-italic.woff2
│   │   │   ├── inter-latin-400-normal.woff
│   │   │   ├── inter-latin-400-normal.woff2
│   │   │   ├── inter-latin-500-italic.woff
│   │   │   ├── inter-latin-500-italic.woff2
│   │   │   ├── inter-latin-500-normal.woff
│   │   │   ├── inter-latin-500-normal.woff2
│   │   │   ├── inter-latin-600-italic.woff
│   │   │   ├── inter-latin-600-italic.woff2
│   │   │   ├── inter-latin-600-normal.woff
│   │   │   ├── inter-latin-600-normal.woff2
│   │   │   ├── inter-latin-700-italic.woff
│   │   │   ├── inter-latin-700-italic.woff2
│   │   │   ├── inter-latin-700-normal.woff
│   │   │   ├── inter-latin-700-normal.woff2
│   │   │   ├── inter-latin-800-italic.woff
│   │   │   ├── inter-latin-800-italic.woff2
│   │   │   ├── inter-latin-800-normal.woff
│   │   │   ├── inter-latin-800-normal.woff2
│   │   │   ├── inter-latin-900-italic.woff
│   │   │   ├── inter-latin-900-italic.woff2
│   │   │   ├── inter-latin-900-normal.woff
│   │   │   ├── inter-latin-900-normal.woff2
│   │   │   ├── inter-latin-ext-100-italic.woff
│   │   │   ├── inter-latin-ext-100-italic.woff2
│   │   │   ├── inter-latin-ext-100-normal.woff
│   │   │   ├── inter-latin-ext-100-normal.woff2
│   │   │   ├── inter-latin-ext-200-italic.woff
│   │   │   ├── inter-latin-ext-200-italic.woff2
│   │   │   ├── inter-latin-ext-200-normal.woff
│   │   │   ├── inter-latin-ext-200-normal.woff2
│   │   │   ├── inter-latin-ext-300-italic.woff
│   │   │   ├── inter-latin-ext-300-italic.woff2
│   │   │   ├── inter-latin-ext-300-normal.woff
│   │   │   ├── inter-latin-ext-300-normal.woff2
│   │   │   ├── inter-latin-ext-400-italic.woff
│   │   │   ├── inter-latin-ext-400-italic.woff2
│   │   │   ├── inter-latin-ext-400-normal.woff
│   │   │   ├── inter-latin-ext-400-normal.woff2
│   │   │   ├── inter-latin-ext-500-italic.woff
│   │   │   ├── inter-latin-ext-500-italic.woff2
│   │   │   ├── inter-latin-ext-500-normal.woff
│   │   │   ├── inter-latin-ext-500-normal.woff2
│   │   │   ├── inter-latin-ext-600-italic.woff
│   │   │   ├── inter-latin-ext-600-italic.woff2
│   │   │   ├── inter-latin-ext-600-normal.woff
│   │   │   ├── inter-latin-ext-600-normal.woff2
│   │   │   ├── inter-latin-ext-700-italic.woff
│   │   │   ├── inter-latin-ext-700-italic.woff2
│   │   │   ├── inter-latin-ext-700-normal.woff
│   │   │   ├── inter-latin-ext-700-normal.woff2
│   │   │   ├── inter-latin-ext-800-italic.woff
│   │   │   ├── inter-latin-ext-800-italic.woff2
│   │   │   ├── inter-latin-ext-800-normal.woff
│   │   │   ├── inter-latin-ext-800-normal.woff2
│   │   │   ├── inter-latin-ext-900-italic.woff
│   │   │   ├── inter-latin-ext-900-italic.woff2
│   │   │   ├── inter-latin-ext-900-normal.woff
│   │   │   ├── inter-latin-ext-900-normal.woff2
│   │   │   ├── inter-vietnamese-100-italic.woff
│   │   │   ├── inter-vietnamese-100-italic.woff2
│   │   │   ├── inter-vietnamese-100-normal.woff
│   │   │   ├── inter-vietnamese-100-normal.woff2
│   │   │   ├── inter-vietnamese-200-italic.woff
│   │   │   ├── inter-vietnamese-200-italic.woff2
│   │   │   ├── inter-vietnamese-200-normal.woff
│   │   │   ├── inter-vietnamese-200-normal.woff2
│   │   │   ├── inter-vietnamese-300-italic.woff
│   │   │   ├── inter-vietnamese-300-italic.woff2
│   │   │   ├── inter-vietnamese-300-normal.woff
│   │   │   ├── inter-vietnamese-300-normal.woff2
│   │   │   ├── inter-vietnamese-400-italic.woff
│   │   │   ├── inter-vietnamese-400-italic.woff2
│   │   │   ├── inter-vietnamese-400-normal.woff
│   │   │   ├── inter-vietnamese-400-normal.woff2
│   │   │   ├── inter-vietnamese-500-italic.woff
│   │   │   ├── inter-vietnamese-500-italic.woff2
│   │   │   ├── inter-vietnamese-500-normal.woff
│   │   │   ├── inter-vietnamese-500-normal.woff2
│   │   │   ├── inter-vietnamese-600-italic.woff
│   │   │   ├── inter-vietnamese-600-italic.woff2
│   │   │   ├── inter-vietnamese-600-normal.woff
│   │   │   ├── inter-vietnamese-600-normal.woff2
│   │   │   ├── inter-vietnamese-700-italic.woff
│   │   │   ├── inter-vietnamese-700-italic.woff2
│   │   │   ├── inter-vietnamese-700-normal.woff
│   │   │   ├── inter-vietnamese-700-normal.woff2
│   │   │   ├── inter-vietnamese-800-italic.woff
│   │   │   ├── inter-vietnamese-800-italic.woff2
│   │   │   ├── inter-vietnamese-800-normal.woff
│   │   │   ├── inter-vietnamese-800-normal.woff2
│   │   │   ├── inter-vietnamese-900-italic.woff
│   │   │   ├── inter-vietnamese-900-italic.woff2
│   │   │   ├── inter-vietnamese-900-normal.woff
│   │   │   └── inter-vietnamese-900-normal.woff2
│   │   ├── app.build.css
│   │   └── app.css
│   ├── js
│   │   ├── app.js
│   │   └── bundle.js
│   ├── partners
│   │   ├── chariow.svg
│   │   ├── publiseer.svg
│   │   └── youscribe.svg
│   └── styles
│       └── grad-blur.css
├── store
│   ├── content
│   │   ├── __init__.py
│   │   └── faqs.py
│   ├── management
│   │   ├── commands
│   │   │   ├── __init__.py
│   │   │   ├── cinetpay_simulate_webhook.py
│   │   │   ├── process_kit_tasks.py
│   │   │   ├── seed_download_assets.py
│   │   │   ├── seed_download_pages.py
│   │   │   ├── seed_ir_categories.py
│   │   │   ├── seed_ir_plus.py
│   │   │   ├── seed_offers_adjust.py
│   │   │   ├── seed_offers_safe.py
│   │   │   ├── seed_prelim.py
│   │   │   └── seed_store.py
│   │   └── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_remove_order_order_id_remove_order_provider_and_more.py
│   │   ├── 0003_clientinquiry_offertier_title_inquirydocument.py
│   │   ├── 0004_payment_paymentevent.py
│   │   ├── 0005_paymentwebhooklog.py
│   │   ├── 0006_add_order_uuid.py
│   │   ├── 0007_fill_order_uuid.py
│   │   ├── 0008_alter_order_uuid.py
│   │   ├── 0009_merge_uuid.py
│   │   ├── 0010_alter_order_uuid.py
│   │   ├── 0011_product_deliverable_file_6x9_and_more.py
│   │   ├── 0012_bonusrequest_and_more.py
│   │   ├── 0013_clientinquiry_context_text_kitprocessingtask.py
│   │   ├── 0014_clientinquiry_ai_doc_clientinquiry_ai_done_at_and_more.py
│   │   └── __init__.py
│   ├── seeds
│   │   ├── __init__.py
│   │   └── ebook_irregularities.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── access.py
│   │   ├── cinetpay.py
│   │   └── kit_builder.py
│   ├── templates
│   │   ├── store
│   │   │   ├── forms
│   │   │   │   ├── kit_inquiry.html
│   │   │   │   └── kit_inquiry_success.html
│   │   │   ├── partials
│   │   │   │   ├── examples_block_carousel.html
│   │   │   │   ├── examples_block_prelim_carousel.html
│   │   │   │   ├── examples_block_table_carousel.html
│   │   │   │   ├── irregularities_table.html
│   │   │   │   └── product_marketing_panel.html
│   │   │   ├── base.html
│   │   │   ├── bonus_claim.html
│   │   │   ├── bonus_landing.html
│   │   │   ├── bonus_prelim_submit.html
│   │   │   ├── bonus_submit.html
│   │   │   ├── bonus_thanks.html
│   │   │   ├── bonus_upload.html
│   │   │   ├── buy_other_methods.html
│   │   │   ├── checkout.html
│   │   │   ├── download_options.html
│   │   │   ├── downloads_list.html
│   │   │   ├── examples.html
│   │   │   ├── examples_prelim.html
│   │   │   ├── kit_inquiry.html
│   │   │   ├── kit_processing_list.html
│   │   │   ├── offers.html
│   │   │   ├── payment_error.html
│   │   │   ├── payment_return.html
│   │   │   ├── payment_success.html
│   │   │   ├── product_detail.html
│   │   │   ├── thank_you.html
│   │   │   ├── training_inquiry.html
│   │   │   ├── training_inquiry_success.html
│   │   │   └── user_orders.html
│   ├── tests
│   │   ├── utils
│   │   │   └── status_helpers.py
│   │   ├── __init__.py
│   │   ├── factories.py
│   │   ├── test_cinetpay_gonogo.py
│   │   ├── test_cinetpay_recipe.py
│   │   ├── test_cinetpay_webhook.py
│   │   ├── test_faqs_render.py
│   │   ├── test_links_and_carousel.py
│   │   ├── test_payment_callback_idempotent.py
│   │   ├── test_payment_return_paid_redirects.py
│   │   └── test_payment_return_unpaid.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── docx_builder.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── forms_bonus.py
│   ├── models.py
│   ├── services.py
│   ├── tasks.py
│   ├── urls.py
│   ├── views.py
│   ├── views_admin_bonus.py
│   ├── views_bonus.py
├── templates
│   ├── ai
│   │   └── prompts
│   │       └── kit_complet_consigne.md
│   ├── 404.html
│   ├── 500.html
│   ├── base.html
│   └── base_error_min.html
├── tests
│   ├── test_commands.py
│   ├── test_integrations_cinetpay.py
│   └── test_smoke.py
├── tmp
│   └── restart.txt
├── var
│   └── sample_orders.csv
├── .env
├── .env.example
├── .flake8
├── .htaccess
├── .pre-commit-config.yaml
├── body.json
├── CHANGEMENTS_2025-10-21.md
├── check_entitlements.py
├── conftest.py
├── CORRECTIONS_CONFIG.md
├── create_entitlement.py
├── debug_cinetpay_signature.md
├── debug_entitlement.py
├── docker-compose.yml
├── DOCUMENTATION_INDEX.md
├── ENV_TEMPLATE.txt
├── FETCH_RECEIPTS_README.md
├── generate_structure.py
├── IMPLEMENTATION_COMPLETE.md
├── manage.py
├── package-lock.json
├── package.json
├── passenger_wsgi.py
├── postcss.config.cjs
├── PRODUCTION_CHECKLIST.md
├── PROJECT_STRUCTURE.md
├── pytest.ini
├── QUICK_START.md
├── README.md
├── README_SQUELETTE_EBOOK.md
├── REFACTORING_SUMMARY.md
├── requirements.txt
├── ROBUSTNESS_GUIDE.md
├── ruff.toml
├── run_fetch_local.ps1
├── run_fetch_local.sh
├── scripts_populate_exemples.py
├── SELAR_REMOVAL_SUMMARY.md
├── SESSION_SUMMARY_2025-10-21.md
├── simple_test.py
├── Squelette Django + Htmx Pour Site Ebook (cinet Pay Mock).pdf
├── tailwind.config.js
├── test_email_sending.py
├── TEST_GUIDE.md
└── test_webhook.py

```

## Notes

- Les fichiers de sauvegarde (`.bak`, `backup-`) sont exclus
- Les dossiers `__pycache__`, `node_modules`, `staticfiles` sont exclus
- L'environnement virtuel (`Active-le`) est exclu
- Les fichiers compressés (`.gz`) sont exclus
- Profondeur maximale: 10 niveaux

## Applications Django

- **config**: Configuration principale du projet (settings, urls, wsgi)
- **core**: Pages principales (home, about, contact, CGV, politique)
- **store**: Gestion des produits, offres, paiements (CinetPay), commandes
- **downloads**: Gestion des téléchargements sécurisés et catégories
- **legal**: Pages légales (mentions légales, etc.)
