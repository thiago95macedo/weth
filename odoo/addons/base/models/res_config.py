import json
import logging
import re

from lxml import etree

from odoo import api, models, _
from odoo.exceptions import AccessError, RedirectWarning, UserError
from odoo.tools import ustr

_logger = logging.getLogger(__name__)


class ResConfigModuleInstallationMixin(object):
    __slots__ = ()

    @api.model
    def _install_modules(self, modules):
        """ Install the requested modules.

        :param modules: a list of tuples (module_name, module_record)
        :return: the next action to execute
        """
        to_install_modules = self.env['ir.module.module']
        to_install_missing_names = []

        for name, module in modules:
            if not module:
                to_install_missing_names.append(name)
            elif module.state == 'uninstalled':
                to_install_modules += module
        result = None
        if to_install_modules:
            result = to_install_modules.button_immediate_install()
        #FIXME: if result is not none, the corresponding todo will be skipped because it was just marked done
        if to_install_missing_names:
            return {
                'type': 'ir.actions.client',
                'tag': 'apps',
                'params': {'modules': to_install_missing_names},
            }

        return result


class ResConfigConfigurable(models.TransientModel):
    ''' Base classes for new-style configuration items

    Configuration items should inherit from this class, implement
    the execute method (and optionally the cancel one) and have
    their view inherit from the related res_config_view_base view.
    '''
    _name = 'res.config'
    _description = 'Config'

    def start(self):
        # pylint: disable=next-method-called
        return self.next()

    def next(self):
        """
        Reload the settings page
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def execute(self):
        """ Method called when the user clicks on the ``Next`` button.

        Execute *must* be overloaded unless ``action_next`` is overloaded
        (which is something you generally don't need to do).

        If ``execute`` returns an action dictionary, that action is executed
        rather than just going to the next configuration item.
        """
        raise NotImplementedError(
            'Configuration items need to implement execute')

    def cancel(self):
        """ Method called when the user click on the ``Skip`` button.

        ``cancel`` should be overloaded instead of ``action_skip``. As with
        ``execute``, if it returns an action dictionary that action is
        executed in stead of the default (going to the next configuration item)

        The default implementation is a NOOP.

        ``cancel`` is also called by the default implementation of
        ``action_cancel``.
        """
        pass

    def action_next(self):
        """ Action handler for the ``next`` event.

        Sets the status of the todo the event was sent from to
        ``done``, calls ``execute`` and -- unless ``execute`` returned
        an action dictionary -- executes the action provided by calling
        ``next``.
        """
        # pylint: disable=next-method-called
        return self.execute() or self.next()

    def action_skip(self):
        """ Action handler for the ``skip`` event.

        Sets the status of the todo the event was sent from to
        ``skip``, calls ``cancel`` and -- unless ``cancel`` returned
        an action dictionary -- executes the action provided by calling
        ``next``.
        """
        # pylint: disable=next-method-called
        return self.cancel() or self.next()

    def action_cancel(self):
        """ Action handler for the ``cancel`` event. That event isn't
        generated by the res.config.view.base inheritable view, the
        inherited view has to overload one of the buttons (or add one
        more).

        Sets the status of the todo the event was sent from to
        ``cancel``, calls ``cancel`` and -- unless ``cancel`` returned
        an action dictionary -- executes the action provided by calling
        ``next``.
        """
        # pylint: disable=next-method-called
        return self.cancel() or self.next()


class ResConfigInstaller(models.TransientModel, ResConfigModuleInstallationMixin):
    """ New-style configuration base specialized for addons selection
    and installation.

    Basic usage
    -----------

    Subclasses can simply define a number of boolean fields. The field names
    should be the names of the addons to install (when selected). Upon action
    execution, selected boolean fields (and those only) will be interpreted as
    addons to install, and batch-installed.

    Additional addons
    -----------------

    It is also possible to require the installation of an additional
    addon set when a specific preset of addons has been marked for
    installation (in the basic usage only, additionals can't depend on
    one another).

    These additionals are defined through the ``_install_if``
    property. This property is a mapping of a collection of addons (by
    name) to a collection of addons (by name) [#]_, and if all the *key*
    addons are selected for installation, then the *value* ones will
    be selected as well. For example::

        _install_if = {
            ('sale','crm'): ['sale_crm'],
        }

    This will install the ``sale_crm`` addon if and only if both the
    ``sale`` and ``crm`` addons are selected for installation.

    You can define as many additionals as you wish, and additionals
    can overlap in key and value. For instance::

        _install_if = {
            ('sale','crm'): ['sale_crm'],
            ('sale','project'): ['sale_service'],
        }

    will install both ``sale_crm`` and ``sale_service`` if all of
    ``sale``, ``crm`` and ``project`` are selected for installation.

    Hook methods
    ------------

    Subclasses might also need to express dependencies more complex
    than that provided by additionals. In this case, it's possible to
    define methods of the form ``_if_%(name)s`` where ``name`` is the
    name of a boolean field. If the field is selected, then the
    corresponding module will be marked for installation *and* the
    hook method will be executed.

    Hook methods take the usual set of parameters (cr, uid, ids,
    context) and can return a collection of additional addons to
    install (if they return anything, otherwise they should not return
    anything, though returning any "falsy" value such as None or an
    empty collection will have the same effect).

    Complete control
    ----------------

    The last hook is to simply overload the ``modules_to_install``
    method, which implements all the mechanisms above. This method
    takes the usual set of parameters (cr, uid, ids, context) and
    returns a ``set`` of addons to install (addons selected by the
    above methods minus addons from the *basic* set which are already
    installed) [#]_ so an overloader can simply manipulate the ``set``
    returned by ``ResConfigInstaller.modules_to_install`` to add or
    remove addons.

    Skipping the installer
    ----------------------

    Unless it is removed from the view, installers have a *skip*
    button which invokes ``action_skip`` (and the ``cancel`` hook from
    ``res.config``). Hooks and additionals *are not run* when skipping
    installation, even for already installed addons.

    Again, setup your hooks accordingly.

    .. [#] note that since a mapping key needs to be hashable, it's
           possible to use a tuple or a frozenset, but not a list or a
           regular set

    .. [#] because the already-installed modules are only pruned at
           the very end of ``modules_to_install``, additionals and
           hooks depending on them *are guaranteed to execute*. Setup
           your hooks accordingly.
    """
    _name = 'res.config.installer'
    _inherit = 'res.config'
    _description = 'Config Installer'

    _install_if = {}

    def already_installed(self):
        """ For each module, check if it's already installed and if it
        is return its name

        :returns: a list of the already installed modules in this
                  installer
        :rtype: [str]
        """
        return [m.name for m in self._already_installed()]

    def _already_installed(self):
        """ For each module (boolean fields in a res.config.installer),
        check if it's already installed (either 'to install', 'to upgrade'
        or 'installed') and if it is return the module's record

        :returns: a list of all installed modules in this installer
        :rtype: recordset (collection of Record)
        """
        selectable = [name for name, field in self._fields.items()
                      if field.type == 'boolean']
        return self.env['ir.module.module'].search([('name', 'in', selectable),
                            ('state', 'in', ['to install', 'installed', 'to upgrade'])])

    def modules_to_install(self):
        """ selects all modules to install:

        * checked boolean fields
        * return values of hook methods. Hook methods are of the form
          ``_if_%(addon_name)s``, and are called if the corresponding
          addon is marked for installation. They take the arguments
          cr, uid, ids and context, and return an iterable of addon
          names
        * additionals, additionals are setup through the ``_install_if``
          class variable. ``_install_if`` is a dict of {iterable:iterable}
          where key and value are iterables of addon names.

          If all the addons in the key are selected for installation
          (warning: addons added through hooks don't count), then the
          addons in the value are added to the set of modules to install
        * not already installed
        """
        base = set(module_name
                   for installer in self.read()
                   for module_name, to_install in installer.items()
                   if self._fields[module_name].type == 'boolean' and to_install)

        hooks_results = set()
        for module in base:
            hook = getattr(self, '_if_%s'% module, None)
            if hook:
                hooks_results.update(hook() or set())

        additionals = set(module
                          for requirements, consequences in self._install_if.items()
                          if base.issuperset(requirements)
                          for module in consequences)

        return (base | hooks_results | additionals) - set(self.already_installed())

    @api.model
    def default_get(self, fields_list):
        ''' If an addon is already installed, check it by default
        '''
        defaults = super(ResConfigInstaller, self).default_get(fields_list)
        return dict(defaults, **dict.fromkeys(self.already_installed(), True))

    @api.model
    def fields_get(self, fields=None, attributes=None):
        """ If an addon is already installed, set it to readonly as
        res.config.installer doesn't handle uninstallations of already
        installed addons
        """
        fields = super(ResConfigInstaller, self).fields_get(fields, attributes=attributes)

        for name in self.already_installed():
            if name not in fields:
                continue
            fields[name].update(
                readonly=True,
                help= ustr(fields[name].get('help', '')) +
                     _('\n\nThis addon is already installed on your system'))
        return fields

    def execute(self):
        to_install = list(self.modules_to_install())
        _logger.info('Selecting addons %s to install', to_install)

        IrModule = self.env['ir.module.module']
        modules = []
        for name in to_install:
            module = IrModule.search([('name', '=', name)], limit=1)
            modules.append((name, module))

        return self._install_modules(modules)


class ResConfigSettings(models.TransientModel, ResConfigModuleInstallationMixin):
    """ Base configuration wizard for application settings.  It provides support for setting
        default values, assigning groups to employee users, and installing modules.
        To make such a 'settings' wizard, define a model like::

            class MyConfigWizard(models.TransientModel):
                _name = 'my.settings'
                _inherit = 'res.config.settings'

                default_foo = fields.type(..., default_model='my.model'),
                group_bar = fields.Boolean(..., group='base.group_user', implied_group='my.group'),
                module_baz = fields.Boolean(...),
                config_qux = fields.Char(..., config_parameter='my.parameter')
                other_field = fields.type(...),

        The method ``execute`` provides some support based on a naming convention:

        *   For a field like 'default_XXX', ``execute`` sets the (global) default value of
            the field 'XXX' in the model named by ``default_model`` to the field's value.

        *   For a boolean field like 'group_XXX', ``execute`` adds/removes 'implied_group'
            to/from the implied groups of 'group', depending on the field's value.
            By default 'group' is the group Employee.  Groups are given by their xml id.
            The attribute 'group' may contain several xml ids, separated by commas.

        *   For a selection field like 'group_XXX' composed of 2 string values ('0' and '1'),
            ``execute`` adds/removes 'implied_group' to/from the implied groups of 'group', 
            depending on the field's value.
            By default 'group' is the group Employee.  Groups are given by their xml id.
            The attribute 'group' may contain several xml ids, separated by commas.

        *   For a boolean field like 'module_XXX', ``execute`` triggers the immediate
            installation of the module named 'XXX' if the field has value ``True``.

        *   For a selection field like 'module_XXX' composed of 2 string values ('0' and '1'), 
            ``execute`` triggers the immediate installation of the module named 'XXX' 
            if the field has the value ``'1'``.

        *   For a field with no specific prefix BUT an attribute 'config_parameter',
            ``execute``` will save its value in an ir.config.parameter (global setting for the
            database).

        *   For the other fields, the method ``execute`` invokes `set_values`.
            Override it to implement the effect of those fields.

        The method ``default_get`` retrieves values that reflect the current status of the
        fields like 'default_XXX', 'group_XXX', 'module_XXX' and config_XXX.
        It also invokes all methods with a name that starts with 'get_default_';
        such methods can be defined to provide current values for other fields.
    """
    _name = 'res.config.settings'
    _description = 'Config Settings'

    def _valid_field_parameter(self, field, name):
        return (
            name in ('default_model', 'config_parameter')
            or field.type in ('boolean', 'selection') and name in ('group', 'implied_group')
            or super()._valid_field_parameter(field, name)
        )

    def copy(self, values):
        raise UserError(_("Cannot duplicate configuration!"), "")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(ResConfigSettings, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        can_install_modules = self.env['ir.module.module'].check_access_rights(
                                    'write', raise_exception=False)

        doc = etree.XML(ret_val['arch'])

        for field in ret_val['fields']:
            if not field.startswith("module_"):
                continue
            for node in doc.xpath("//field[@name='%s']" % field):
                if not can_install_modules:
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))

        ret_val['arch'] = etree.tostring(doc, encoding='unicode')
        return ret_val

    def onchange_module(self, field_value, module_name):
        ModuleSudo = self.env['ir.module.module'].sudo()
        modules = ModuleSudo.search(
            [('name', '=', module_name.replace("module_", '')),
            ('state', 'in', ['to install', 'installed', 'to upgrade'])])

        if modules and not int(field_value):
            deps = modules.sudo().downstream_dependencies()
            dep_names = (deps | modules).mapped('shortdesc')
            message = '\n'.join(dep_names)
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _('Disabling this option will also uninstall the following modules \n%s', message),
                }
            }
        return {}

    def _register_hook(self):
        """ Add an onchange method for each module field. """
        def make_method(name):
            return lambda self: self.onchange_module(self[name], name)

        for name in self._fields:
            if name.startswith('module_'):
                method = make_method(name)
                self._onchange_methods[name].append(method)

    @api.model
    def _get_classified_fields(self):
        """ return a dictionary with the fields classified by category::

                {   'default': [('default_foo', 'model', 'foo'), ...],
                    'group':   [('group_bar', [browse_group], browse_implied_group), ...],
                    'module':  [('module_baz', browse_module), ...],
                    'config':  [('config_qux', 'my.parameter'), ...],
                    'other':   ['other_field', ...],
                }
        """
        IrModule = self.env['ir.module.module']
        Groups = self.env['res.groups']
        ref = self.env.ref

        defaults, groups, modules, configs, others = [], [], [], [], []
        for name, field in self._fields.items():
            if name.startswith('default_'):
                if not hasattr(field, 'default_model'):
                    raise Exception("Field %s without attribute 'default_model'" % field)
                defaults.append((name, field.default_model, name[8:]))
            elif name.startswith('group_'):
                if field.type not in ('boolean', 'selection'):
                    raise Exception("Field %s must have type 'boolean' or 'selection'" % field)
                if not hasattr(field, 'implied_group'):
                    raise Exception("Field %s without attribute 'implied_group'" % field)
                field_group_xmlids = getattr(field, 'group', 'base.group_user').split(',')
                field_groups = Groups.concat(*(ref(it) for it in field_group_xmlids))
                groups.append((name, field_groups, ref(field.implied_group)))
            elif name.startswith('module_'):
                if field.type not in ('boolean', 'selection'):
                    raise Exception("Field %s must have type 'boolean' or 'selection'" % field)
                module = IrModule.sudo().search([('name', '=', name[7:])], limit=1)
                modules.append((name, module))
            elif hasattr(field, 'config_parameter'):
                if field.type not in ('boolean', 'integer', 'float', 'char', 'selection', 'many2one'):
                    raise Exception("Field %s must have type 'boolean', 'integer', 'float', 'char', 'selection' or 'many2one'" % field)
                configs.append((name, field.config_parameter))
            else:
                others.append(name)

        return {'default': defaults, 'group': groups, 'module': modules, 'config': configs, 'other': others}

    def get_values(self):
        """
        Return values for the fields other that `default`, `group` and `module`
        """
        return {}

    @api.model
    def default_get(self, fields):
        IrDefault = self.env['ir.default']
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        classified = self._get_classified_fields()

        res = super(ResConfigSettings, self).default_get(fields)

        # defaults: take the corresponding default value they set
        for name, model, field in classified['default']:
            value = IrDefault.get(model, field)
            if value is not None:
                res[name] = value

        # groups: which groups are implied by the group Employee
        for name, groups, implied_group in classified['group']:
            res[name] = all(implied_group in group.implied_ids for group in groups)
            if self._fields[name].type == 'selection':
                res[name] = str(int(res[name]))     # True, False -> '1', '0'

        # modules: which modules are installed/to install
        for name, module in classified['module']:
            res[name] = module.state in ('installed', 'to install', 'to upgrade')
            if self._fields[name].type == 'selection':
                res[name] = str(int(res[name]))     # True, False -> '1', '0'

        # config: get & convert stored ir.config_parameter (or default)
        WARNING_MESSAGE = "Error when converting value %r of field %s for ir.config.parameter %r"
        for name, icp in classified['config']:
            field = self._fields[name]
            value = IrConfigParameter.get_param(icp, field.default(self) if field.default else False)
            if value is not False:
                if field.type == 'many2one':
                    try:
                        # Special case when value is the id of a deleted record, we do not want to
                        # block the settings screen
                        value = self.env[field.comodel_name].browse(int(value)).exists().id
                    except (ValueError, TypeError):
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = False
                elif field.type == 'integer':
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = 0
                elif field.type == 'float':
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = 0.0
                elif field.type == 'boolean':
                    value = bool(value)
            res[name] = value

        res.update(self.get_values())

        return res

    def set_values(self):
        """
        Set values for the fields other that `default`, `group` and `module`
        """
        self = self.with_context(active_test=False)
        classified = self._get_classified_fields()

        # default values fields
        IrDefault = self.env['ir.default'].sudo()
        for name, model, field in classified['default']:
            if isinstance(self[name], models.BaseModel):
                if self._fields[name].type == 'many2one':
                    value = self[name].id
                else:
                    value = self[name].ids
            else:
                value = self[name]
            IrDefault.set(model, field, value)

        # group fields: modify group / implied groups
        current_settings = self.default_get(list(self.fields_get()))
        with self.env.norecompute():
            for name, groups, implied_group in sorted(classified['group'], key=lambda k: self[k[0]]):
                groups = groups.sudo()
                implied_group = implied_group.sudo()
                if self[name] == current_settings[name]:
                    continue
                if int(self[name]):
                    groups.write({'implied_ids': [(4, implied_group.id)]})
                else:
                    groups.write({'implied_ids': [(3, implied_group.id)]})
                    implied_group.write({'users': [(3, user.id) for user in groups.users]})

        # config fields: store ir.config_parameters
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        for name, icp in classified['config']:
            field = self._fields[name]
            value = self[name]
            if field.type == 'char':
                # storing developer keys as ir.config_parameter may lead to nasty
                # bugs when users leave spaces around them
                value = (value or "").strip() or False
            elif field.type in ('integer', 'float'):
                value = repr(value) if value else False
            elif field.type == 'many2one':
                # value is a (possibly empty) recordset
                value = value.id
            IrConfigParameter.set_param(icp, value)

    def execute(self):
        """
        Called when settings are saved.

        This method will call `set_values` and will install/uninstall any modules defined by
        `module_` Boolean fields and then trigger a web client reload.

        .. warning::

            This method **SHOULD NOT** be overridden, in most cases what you want to override is
            `~set_values()` since `~execute()` does little more than simply call `~set_values()`.

            The part that installs/uninstalls modules **MUST ALWAYS** be at the end of the
            transaction, otherwise there's a big risk of registry <-> database desynchronisation.
        """
        self.ensure_one()
        if not self.env.is_admin():
            raise AccessError(_("Only administrators can change the settings"))

        self = self.with_context(active_test=False)
        classified = self._get_classified_fields()

        self.set_values()

        # module fields: install/uninstall the selected modules
        to_install = []
        to_uninstall_modules = self.env['ir.module.module']
        lm = len('module_')
        for name, module in classified['module']:
            if int(self[name]):
                to_install.append((name[lm:], module))
            else:
                if module and module.state in ('installed', 'to upgrade'):
                    to_uninstall_modules += module

        if to_install or to_uninstall_modules:
            self.flush()

        if to_uninstall_modules:
            to_uninstall_modules.button_immediate_uninstall()

        installation_status = self._install_modules(to_install)

        if installation_status or to_uninstall_modules:
            # After the uninstall/install calls, the registry and environments
            # are no longer valid. So we reset the environment.
            self.env.reset()
            self = self.env()[self._name]

        # pylint: disable=next-method-called
        config = self.env['res.config'].next() or {}
        if config.get('type') not in ('ir.actions.act_window_close',):
            return config

        # force client-side reload (update user menu and current view)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def cancel(self):
        # ignore the current record, and send the action to reopen the view
        actions = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        if actions:
            return actions.read()[0]
        return {}

    def name_get(self):
        """ Override name_get method to return an appropriate configuration wizard
        name, and not the generated name."""
        action = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        name = action.name or self._name
        return [(record.id, name) for record in self]

    @api.model
    def get_option_path(self, menu_xml_id):
        """
        Fetch the path to a specified configuration view and the action id to access it.

        :param string menu_xml_id: the xml id of the menuitem where the view is located,
            structured as follows: module_name.menuitem_xml_id (e.g.: "sales_team.menu_sale_config")
        :return tuple:
            - t[0]: string: full path to the menuitem (e.g.: "Settings/Configuration/Sales")
            - t[1]: int or long: id of the menuitem's action
        """
        ir_ui_menu = self.env.ref(menu_xml_id)
        return (ir_ui_menu.complete_name, ir_ui_menu.action.id)

    @api.model
    def get_option_name(self, full_field_name):
        """
        Fetch the human readable name of a specified configuration option.

        :param string full_field_name: the full name of the field, structured as follows:
            model_name.field_name (e.g.: "sale.config.settings.fetchmail_lead")
        :return string: human readable name of the field (e.g.: "Create leads from incoming mails")
        """
        model_name, field_name = full_field_name.rsplit('.', 1)
        return self.env[model_name].fields_get([field_name])[field_name]['string']

    @api.model
    def get_config_warning(self, msg):
        """
        Helper: return a Warning exception with the given message where the %(field:xxx)s
        and/or %(menu:yyy)s are replaced by the human readable field's name and/or menuitem's
        full path.

        Usage:
        ------
        Just include in your error message %(field:model_name.field_name)s to obtain the human
        readable field's name, and/or %(menu:module_name.menuitem_xml_id)s to obtain the menuitem's
        full path.

        Example of use:
        ---------------
        from odoo.addons.base.models.res_config import get_warning_config
        raise get_warning_config(cr, _("Error: this action is prohibited. You should check the field %(field:sale.config.settings.fetchmail_lead)s in %(menu:sales_team.menu_sale_config)s."), context=context)

        This will return an exception containing the following message:
            Error: this action is prohibited. You should check the field Create leads from incoming mails in Settings/Configuration/Sales.

        What if there is another substitution in the message already?
        -------------------------------------------------------------
        You could have a situation where the error message you want to upgrade already contains a substitution. Example:
            Cannot find any account journal of %s type for this company.\n\nYou can create one in the menu: \nConfiguration\Journals\Journals.
        What you want to do here is simply to replace the path by %menu:account.menu_account_config)s, and leave the rest alone.
        In order to do that, you can use the double percent (%%) to escape your new substitution, like so:
            Cannot find any account journal of %s type for this company.\n\nYou can create one in the %%(menu:account.menu_account_config)s.
        """
        self = self.sudo()

        # Process the message
        # 1/ find the menu and/or field references, put them in a list
        regex_path = r'%\(((?:menu|field):[a-z_\.]*)\)s'
        references = re.findall(regex_path, msg, flags=re.I)

        # 2/ fetch the menu and/or field replacement values (full path and
        #    human readable field's name) and the action_id if any
        values = {}
        action_id = None
        for item in references:
            ref_type, ref = item.split(':')
            if ref_type == 'menu':
                values[item], action_id = self.get_option_path(ref)
            elif ref_type == 'field':
                values[item] = self.get_option_name(ref)

        # 3/ substitute and return the result
        if (action_id):
            return RedirectWarning(msg % values, action_id, _('Go to the configuration panel'))
        return UserError(msg % values)

    @api.model
    def create(self, values):
        # Optimisation: saving a res.config.settings even without changing any
        # values will trigger the write of all related values. This in turn may
        # trigger chain of further recomputation. To avoid it, delete values
        # that were not changed.
        for field in self._fields.values():
            if not (field.name in values and field.related and not field.readonly):
                continue
            # we write on a related field like
            # qr_code = fields.Boolean(related='company_id.qr_code', readonly=False)
            fname0 = field.related[0]
            if fname0 not in values:
                continue

            # determine the current value
            field0 = self._fields[fname0]
            old_value = field0.convert_to_record(
                field0.convert_to_cache(values[fname0], self), self)
            for fname in field.related[1:]:
                old_value = next(iter(old_value), old_value)[fname]

            # determine the new value
            new_value = field.convert_to_record(
                field.convert_to_cache(values[field.name], self), self)

            # drop if the value is the same
            if old_value == new_value:
                values.pop(field.name)

        return super(ResConfigSettings, self).create(values)
