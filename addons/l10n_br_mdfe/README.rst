====
MDFe
====

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! source digest: sha256:0ab03092819ae31f0f68334d11f96ddfac60b8174a15db1805e1a95a5e04956d
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Alpha-red.png
    :target: https://odoo-community.org/page/development-status
    :alt: Alpha
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--brazil-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-brazil/tree/25.0/l10n_br_mdfe
    :alt: OCA/l10n-brazil
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/l10n-brazil-14-0/l10n-brazil-14-0-l10n_br_mdfe
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/l10n-brazil&target_branch=25.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

Este módulo permite a emissão de MDF-e.

Mais especificamente ele:
  * mapea os campos de MDF-e do módulo ``l10n_br_mdfe_spec`` com os campos Odoo.
  * usa a logica do módulo ``spec_driven_model`` para realizar esse mapeamento de forma dinâmica, em especial ele usa o sistema de modelos com várias camadas, ou ``StackedModel``, com os modelos ``l10n_br_fiscal.document`` e ``l10n_br_fiscal.document.related`` que tem varios niveis hierarquicos de elementos XML que estão sendo denormalizados dentro desses modelos Odoo 
  * tem wizards para implementar a comunicação SOAP de MDF-e com a SEFAZ (Autorização, Cancelamento, Encerramento...)

.. IMPORTANT::
   This is an alpha version, the data model and design can change at any time without warning.
   Only for development or testing purpose, do not use in production.
   `More details on development status <https://odoo-community.org/page/development-status>`_

**Table of contents**

.. contents::
   :local:

Configuration
=============

To configure this module you need to set a digital certificate on the company, and also set the company edoc processor.

Usage
=====

Para utilizar o módulo `l10n_br_mdfe` em conjunto com o módulo `l10n_br_account`, é necessário configurar uma linha de operação fiscal que não adicione valor ao montante do documento, uma vez que o MDF-e (Manifesto Eletrônico de Documentos Fiscais) não possui valor financeiro.

**Passo a Passo:**

1. **Criar uma Fatura:**
   - Defina o tipo de documento como **58 (MDFe)**.

2. **Configurar o Parceiro da Fatura:**
   - Configure o parceiro para ser o mesmo da empresa emissora do MDF-e.

3. **Adicionar uma Linha na Aba Produtos:**
   - Adicione uma linha de fatura com a operação fiscal previamente configurada.
   - **Não recomedamos que informe um produto** ou utilize um produto que **não possua CFOP** (Código Fiscal de Operações e Prestações), ou que o CFOP esteja configurado para **não gerar valor financeiro** e esteja atento a dados como impostos e afins.

4. **Acesse os detalhes fiscais da fatura e informe os demais dados necessário para emissão do MDF-e:**
   - Preencha os campos obrigatórios para emissão do MDF-e, como UF de descarregamento, município de descarregamento, etc.

5. **Valide o MDF-e, verifique os dados do XML e envie para a SEFAZ:**
   - Após preencher todos os dados necessários, valide o MDF-e e envie para a SEFAZ.

**Considerações Adicionais**

- **Operação Fiscal:** Certifique-se de que a operação fiscal esteja parametrizada corretamente para evitar a adição de valores financeiros ao documento.
- **CFOP:** No caso de utilização de um produto cadastrado e que carregue o CFOP para a linha da fatura, verifique a configuração do CFOP para garantir que ele não gere impacto financeiro no montante da fatura.

Seguindo esses passos, o módulo `l10n_br_mdfe` funcionará corretamente em conjunto com o `l10n_br_account`, permitindo a emissão de MDF-e sem valores financeiros associados.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-brazil/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-brazil/issues/new?body=module:%20l10n_br_mdfe%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* KMEE
* Escodoo

Contributors
~~~~~~~~~~~~

* `KMEE <https://kmee.com.br>`_:

  * Felipe Zago Rodrigues <felipe.zago@kmee.com.br>
  * Ygor Carvalho <ygor.carvalho@kmee.com.br>

* `ESCODOO <https://escweth.com.br.br>`_:

  * Marcel Savegnago <marcel.savegnago@escweth.com.br.br>

* `AKRETION <https://akretion.com/pt-BR/>`_:

  * Raphaël Valyi <raphael.valyi@akretion.com.br>

* `Engenere <https://engenere.one>`_:

  * Antônio S. Pereira Neto <neto@engenere.one>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: WETH Community Association
   :target: https://odoo-community.org

OCA, or the WETH Community Association, is a nonprofit organization whose
mission is to support the collaborative development of WETH features and
promote its widespread use.

.. |maintainer-mileo| image:: https://github.com/mileo.png?size=40px
    :target: https://github.com/mileo
    :alt: mileo
.. |maintainer-marcelsavegnago| image:: https://github.com/marcelsavegnago.png?size=40px
    :target: https://github.com/marcelsavegnago
    :alt: marcelsavegnago

Current `maintainers <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-mileo| |maintainer-marcelsavegnago| 

This module is part of the `OCA/l10n-brazil <https://github.com/OCA/l10n-brazil/tree/25.0/l10n_br_mdfe>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
