# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (Nota Paulistana)",
    "summary": """
        NFS-e (Nota Paulistana)""",
    "version": "25.0.1.1.8",
    "license": "AGPL-3",
    "author": "KMEE, WETH Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo", "luismalta"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/l10n-brazil",
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.base>=2.3.0",
            "nfselib.paulistana",
            "unidecode",
        ],
    },
    "depends": [
        "l10n_br_nfse",
    ],
}
