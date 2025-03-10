import base64
import datetime
import json
import os
import logging
import pytz
import requests
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers

from itertools import islice
from werkzeug import urls
from xml.etree import ElementTree as ET

import odoo

from odoo import http, models, fields, _
from odoo.http import request
from odoo.tools import OrderedSet
from odoo.addons.http_routing.models.ir_http import slug, slugify, _guess_mimetype
from odoo.addons.web.controllers.main import Binary
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.portal.controllers.web import Home

logger = logging.getLogger(__name__)

# Completely arbitrary limits
MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT = IMAGE_LIMITS = (1024, 768)
LOC_PER_SITEMAP = 45000
SITEMAP_CACHE_TIME = datetime.timedelta(hours=12)


class QueryURL(object):
    def __init__(self, path='', path_args=None, **args):
        self.path = path
        self.args = args
        self.path_args = OrderedSet(path_args or [])

    def __call__(self, path=None, path_args=None, **kw):
        path = path or self.path
        for key, value in self.args.items():
            kw.setdefault(key, value)
        path_args = OrderedSet(path_args or []) | self.path_args
        paths, fragments = {}, []
        for key, value in kw.items():
            if value and key in path_args:
                if isinstance(value, models.BaseModel):
                    paths[key] = slug(value)
                else:
                    paths[key] = u"%s" % value
            elif value:
                if isinstance(value, list) or isinstance(value, set):
                    fragments.append(werkzeug.urls.url_encode([(key, item) for item in value]))
                else:
                    fragments.append(werkzeug.urls.url_encode([(key, value)]))
        for key in path_args:
            value = paths.get(key)
            if value is not None:
                path += '/' + key + '/' + value
        if fragments:
            path += '?' + '&'.join(fragments)
        return path


class Website(Home):

    @http.route('/', type='http', auth="public", website=True, sitemap=True)
    def index(self, **kw):
        # prefetch all menus (it will prefetch website.page too)
        top_menu = request.website.menu_id

        homepage = request.website.homepage_id
        if homepage and (homepage.sudo().is_visible or request.env.user.has_group('base.group_user')) and homepage.url != '/':
            return request.env['ir.http'].reroute(homepage.url)

        website_page = request.env['ir.http']._serve_page()
        if website_page:
            return website_page
        else:
            first_menu = top_menu and top_menu.child_id and top_menu.child_id.filtered(lambda menu: menu.is_visible)
            if first_menu and first_menu[0].url not in ('/', '', '#') and (not (first_menu[0].url.startswith(('/?', '/#', ' ')))):
                return request.redirect(first_menu[0].url)

        raise request.not_found()

    @http.route('/website/force/<int:website_id>', type='http', auth="user", website=True, sitemap=False, multilang=False)
    def website_force(self, website_id, path='/', isredir=False, **kw):
        """ To switch from a website to another, we need to force the website in
        session, AFTER landing on that website domain (if set) as this will be a
        different session.
        """
        parse = werkzeug.urls.url_parse
        safe_path = parse(path).path

        if not (request.env.user.has_group('website.group_multi_website')
           and request.env.user.has_group('website.group_website_publisher')):
            # The user might not be logged in on the forced website, so he won't
            # have rights. We just redirect to the path as the user is already
            # on the domain (basically a no-op as it won't change domain or
            # force website).
            # Website 1 : 127.0.0.1 (admin)
            # Website 2 : 127.0.0.2 (not logged in)
            # Click on "Website 2" from Website 1
            return request.redirect(safe_path)

        website = request.env['website'].browse(website_id)

        if not isredir and website.domain:
            domain_from = request.httprequest.environ.get('HTTP_HOST', '')
            domain_to = parse(website._get_http_domain()).netloc
            if domain_from != domain_to:
                # redirect to correct domain for a correct routing map
                url_to = urls.url_join(website._get_http_domain(), '/website/force/%s?isredir=1&path=%s' % (website.id, safe_path))
                return request.redirect(url_to)
        website._force()
        return request.redirect(safe_path)

    # ------------------------------------------------------
    # Login - overwrite of the web login so that regular users are redirected to the backend
    # while portal users are redirected to the frontend by default
    # ------------------------------------------------------

    def _login_redirect(self, uid, redirect=None):
        """ Redirect regular users (employees) to the backend) and others to
        the frontend
        """
        if not redirect and request.params.get('login_success'):
            if request.env['res.users'].browse(uid).has_group('base.group_user'):
                redirect = '/web?' + request.httprequest.query_string.decode()
            else:
                redirect = '/my'
        return super()._login_redirect(uid, redirect=redirect)

    # Force website=True + auth='public', required for login form layout
    @http.route(website=True, auth="public", sitemap=False)
    def web_login(self, *args, **kw):
        return super().web_login(*args, **kw)

    # ------------------------------------------------------
    # Business
    # ------------------------------------------------------

    @http.route('/website/get_languages', type='json', auth="user", website=True)
    def website_languages(self, **kwargs):
        return [(lg.code, lg.url_code, lg.name) for lg in request.website.language_ids]

    @http.route('/website/lang/<lang>', type='http', auth="public", website=True, multilang=False)
    def change_lang(self, lang, r='/', **kwargs):
        """ :param lang: supposed to be value of `url_code` field """
        r = request.website._get_relative_url(r)
        if lang == 'default':
            lang = request.website.default_lang_id.url_code
            r = '/%s%s' % (lang, r or '/')
        redirect = werkzeug.utils.redirect(r or ('/%s' % lang), 303)
        lang_code = request.env['res.lang']._lang_get_code(lang)
        redirect.set_cookie('frontend_lang', lang_code)
        return redirect

    @http.route(['/website/country_infos/<model("res.country"):country>'], type='json', auth="public", methods=['POST'], website=True)
    def country_infos(self, country, **kw):
        fields = country.get_address_fields()
        return dict(fields=fields, states=[(st.id, st.name, st.code) for st in country.state_ids], phone_code=country.phone_code)

    @http.route(['/robots.txt'], type='http', auth="public", website=True, sitemap=False)
    def robots(self, **kwargs):
        return request.render('website.robots', {'url_root': request.httprequest.url_root}, mimetype='text/plain')

    @http.route('/sitemap.xml', type='http', auth="public", website=True, multilang=False, sitemap=False)
    def sitemap_xml_index(self, **kwargs):
        current_website = request.website
        Attachment = request.env['ir.attachment'].sudo()
        View = request.env['ir.ui.view'].sudo()
        mimetype = 'application/xml;charset=utf-8'
        content = None

        def create_sitemap(url, content):
            return Attachment.create({
                'datas': base64.b64encode(content),
                'mimetype': mimetype,
                'type': 'binary',
                'name': url,
                'url': url,
            })
        dom = [('url', '=', '/sitemap-%d.xml' % current_website.id), ('type', '=', 'binary')]
        sitemap = Attachment.search(dom, limit=1)
        if sitemap:
            # Check if stored version is still valid
            create_date = fields.Datetime.from_string(sitemap.create_date)
            delta = datetime.datetime.now() - create_date
            if delta < SITEMAP_CACHE_TIME:
                content = base64.b64decode(sitemap.datas)

        if not content:
            # Remove all sitemaps in ir.attachments as we're going to regenerated them
            dom = [('type', '=', 'binary'), '|', ('url', '=like', '/sitemap-%d-%%.xml' % current_website.id),
                   ('url', '=', '/sitemap-%d.xml' % current_website.id)]
            sitemaps = Attachment.search(dom)
            sitemaps.unlink()

            pages = 0
            locs = request.website.with_context(_filter_duplicate_pages=True).with_user(request.website.user_id)._enumerate_pages()
            while True:
                values = {
                    'locs': islice(locs, 0, LOC_PER_SITEMAP),
                    'url_root': request.httprequest.url_root[:-1],
                }
                urls = View._render_template('website.sitemap_locs', values)
                if urls.strip():
                    content = View._render_template('website.sitemap_xml', {'content': urls})
                    pages += 1
                    last_sitemap = create_sitemap('/sitemap-%d-%d.xml' % (current_website.id, pages), content)
                else:
                    break

            if not pages:
                return request.not_found()
            elif pages == 1:
                # rename the -id-page.xml => -id.xml
                last_sitemap.write({
                    'url': "/sitemap-%d.xml" % current_website.id,
                    'name': "/sitemap-%d.xml" % current_website.id,
                })
            else:
                # TODO: in master/saas-15, move current_website_id in template directly
                pages_with_website = ["%d-%d" % (current_website.id, p) for p in range(1, pages + 1)]

                # Sitemaps must be split in several smaller files with a sitemap index
                content = View._render_template('website.sitemap_index_xml', {
                    'pages': pages_with_website,
                    'url_root': request.httprequest.url_root,
                })
                create_sitemap('/sitemap-%d.xml' % current_website.id, content)

        return request.make_response(content, [('Content-Type', mimetype)])

    def sitemap_website_info(env, rule, qs):
        website = env['website'].get_current_website()
        if not (
            website.viewref('website.website_info', False).active
            and website.viewref('website.show_website_info', False).active
        ):
            # avoid 404 or blank page in sitemap
            return False

        if not qs or qs.lower() in '/website/info':
            yield {'loc': '/website/info'}

    @http.route('/website/info', type='http', auth="public", website=True, sitemap=sitemap_website_info)
    def website_info(self, **kwargs):
        if not request.website.viewref('website.website_info', False).active:
            # Deleted or archived view (through manual operation in backend).
            # Don't check `show_website_info` view: still need to access if
            # disabled to be able to enable it through the customize show.
            raise request.not_found()

        Module = request.env['ir.module.module'].sudo()
        apps = Module.search([('state', '=', 'installed'), ('application', '=', True)])
        l10n = Module.search([('state', '=', 'installed'), ('name', '=like', 'l10n_%')])
        values = {
            'apps': apps,
            'l10n': l10n,
            'version': odoo.service.common.exp_version()
        }
        return request.render('website.website_info', values)

    @http.route(['/website/social/<string:social>'], type='http', auth="public", website=True, sitemap=False)
    def social(self, social, **kwargs):
        url = getattr(request.website, 'social_%s' % social, False)
        if not url:
            raise werkzeug.exceptions.NotFound()
        return request.redirect(url)

    @http.route('/website/get_suggested_links', type='json', auth="user", website=True)
    def get_suggested_link(self, needle, limit=10):
        current_website = request.website

        matching_pages = []
        for page in current_website.with_context(_filter_duplicate_pages=True).search_pages(needle, limit=int(limit)):
            matching_pages.append({
                'value': page['loc'],
                'label': 'name' in page and '%s (%s)' % (page['loc'], page['name']) or page['loc'],
            })
        matching_urls = set(map(lambda match: match['value'], matching_pages))

        matching_last_modified = []
        last_modified_pages = current_website.with_context(_filter_duplicate_pages=True)._get_website_pages(order='write_date desc', limit=5)
        for url, name in last_modified_pages.mapped(lambda p: (p.url, p.name)):
            if needle.lower() in name.lower() or needle.lower() in url.lower() and url not in matching_urls:
                matching_last_modified.append({
                    'value': url,
                    'label': '%s (%s)' % (url, name),
                })

        suggested_controllers = []
        for name, url, mod in current_website.get_suggested_controllers():
            if needle.lower() in name.lower() or needle.lower() in url.lower():
                module_sudo = mod and request.env.ref('base.module_%s' % mod, False).sudo()
                icon = mod and "<img src='%s' width='24px' height='24px' class='mr-2 rounded' /> " % (module_sudo and module_sudo.icon or mod) or ''
                suggested_controllers.append({
                    'value': url,
                    'label': '%s%s (%s)' % (icon, url, name),
                })

        return {
            'matching_pages': sorted(matching_pages, key=lambda o: o['label']),
            'others': [
                dict(title=_('Last modified pages'), values=matching_last_modified),
                dict(title=_('Apps url'), values=suggested_controllers),
            ]
        }

    @http.route('/website/snippet/filters', type='json', auth='public', website=True)
    def get_dynamic_filter(self, filter_id, template_key, limit=None, search_domain=None):
        dynamic_filter = request.env['website.snippet.filter'].sudo().search(
            [('id', '=', filter_id)] + request.website.website_domain()
        )
        return dynamic_filter and dynamic_filter.render(template_key, limit, search_domain) or ''

    @http.route('/website/snippet/options_filters', type='json', auth='user', website=True)
    def get_dynamic_snippet_filters(self):
        dynamic_filter = request.env['website.snippet.filter'].sudo().search_read(
            request.website.website_domain(), ['id', 'name', 'limit']
        )
        return dynamic_filter

    @http.route('/website/snippet/filter_templates', type='json', auth='public', website=True)
    def get_dynamic_snippet_templates(self, filter_id=False):
        # todo: if filter_id.model -> filter template
        templates = request.env['ir.ui.view'].sudo().search_read(
            [['key', 'ilike', '.dynamic_filter_template_'], ['type', '=', 'qweb']], ['key', 'name']
        )
        return templates

    # ------------------------------------------------------
    # Edit
    # ------------------------------------------------------

    @http.route(['/website/pages', '/website/pages/page/<int:page>'], type='http', auth="user", website=True)
    def pages_management(self, page=1, sortby='url', search='', **kw):
        # only website_designer should access the page Management
        if not request.env.user.has_group('website.group_website_designer'):
            raise werkzeug.exceptions.NotFound()

        Page = request.env['website.page']
        searchbar_sortings = {
            'url': {'label': _('Sort by Url'), 'order': 'url'},
            'name': {'label': _('Sort by Name'), 'order': 'name'},
        }
        # default sortby order
        sort_order = searchbar_sortings.get(sortby, 'url')['order'] + ', website_id desc, id'

        domain = request.website.website_domain()
        if search:
            domain += ['|', ('name', 'ilike', search), ('url', 'ilike', search)]

        pages = Page.search(domain, order=sort_order)
        if sortby != 'url' or not request.env.user.has_group('website.group_multi_website'):
            pages = pages.filtered(pages._is_most_specific_page)
        pages_count = len(pages)

        step = 50
        pager = portal_pager(
            url="/website/pages",
            url_args={'sortby': sortby},
            total=pages_count,
            page=page,
            step=step
        )

        pages = pages[(page - 1) * step:page * step]

        values = {
            'pager': pager,
            'pages': pages,
            'search': search,
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
        }
        return request.render("website.list_website_pages", values)

    @http.route(['/website/add/', '/website/add/<path:path>'], type='http', auth="user", website=True, methods=['POST'])
    def pagenew(self, path="", noredirect=False, add_menu=False, template=False, **kwargs):
        # for supported mimetype, get correct default template
        _, ext = os.path.splitext(path)
        ext_special_case = ext and ext in _guess_mimetype() and ext != '.html'

        if not template and ext_special_case:
            default_templ = 'website.default_%s' % ext.lstrip('.')
            if request.env.ref(default_templ, False):
                template = default_templ

        template = template and dict(template=template) or {}
        page = request.env['website'].new_page(path, add_menu=add_menu, **template)
        url = page['url']
        if noredirect:
            return werkzeug.wrappers.Response(url, mimetype='text/plain')

        if ext_special_case:  # redirect non html pages to backend to edit
            return werkzeug.utils.redirect('/web#id=' + str(page.get('view_id')) + '&view_type=form&model=ir.ui.view')
        return werkzeug.utils.redirect(url + "?enable_editor=1")

    @http.route("/website/get_switchable_related_views", type="json", auth="user", website=True)
    def get_switchable_related_views(self, key):
        views = request.env["ir.ui.view"].get_related_views(key, bundles=False).filtered(lambda v: v.customize_show)
        views = views.sorted(key=lambda v: (v.inherit_id.id, v.name))
        return views.with_context(display_website=False).read(['name', 'id', 'key', 'xml_id', 'active', 'inherit_id'])

    @http.route('/website/toggle_switchable_view', type='json', auth='user', website=True)
    def toggle_switchable_view(self, view_key):
        if request.website.user_has_groups('website.group_website_designer'):
            request.website.viewref(view_key).toggle_active()
        else:
            return werkzeug.exceptions.Forbidden()

    @http.route('/website/reset_template', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def reset_template(self, view_id, mode='soft', redirect='/', **kwargs):
        """ This method will try to reset a broken view.
        Given the mode, the view can either be:
        - Soft reset: restore to previous architeture.
        - Hard reset: it will read the original `arch` from the XML file if the
        view comes from an XML file (arch_fs).
        """
        view = request.env['ir.ui.view'].browse(int(view_id))
        # Deactivate COW to not fix a generic view by creating a specific
        view.with_context(website_id=None).reset_arch(mode)
        return request.redirect(redirect)

    @http.route(['/website/publish'], type='json', auth="user", website=True)
    def publish(self, id, object):
        Model = request.env[object]
        record = Model.browse(int(id))

        values = {}
        if 'website_published' in Model._fields:
            values['website_published'] = not record.website_published
            record.write(values)
            return bool(record.website_published)
        return False

    @http.route(['/website/seo_suggest'], type='json', auth="user", website=True)
    def seo_suggest(self, keywords=None, lang=None):
        language = lang.split("_")
        url = "http://google.com/complete/search"
        try:
            req = requests.get(url, params={
                'ie': 'utf8', 'oe': 'utf8', 'output': 'toolbar', 'q': keywords, 'hl': language[0], 'gl': language[1]})
            req.raise_for_status()
            response = req.content
        except IOError:
            return []
        xmlroot = ET.fromstring(response)
        return json.dumps([sugg[0].attrib['data'] for sugg in xmlroot if len(sugg) and sugg[0].attrib['data']])

    @http.route(['/website/get_seo_data'], type='json', auth="user", website=True)
    def get_seo_data(self, res_id, res_model):
        if not request.env.user.has_group('website.group_website_publisher'):
            raise werkzeug.exceptions.Forbidden()

        fields = ['website_meta_title', 'website_meta_description', 'website_meta_keywords', 'website_meta_og_img']
        if res_model == 'website.page':
            fields.extend(['website_indexed', 'website_id'])

        record = request.env[res_model].browse(res_id)
        res = record._read_format(fields)[0]
        res['has_social_default_image'] = request.website.has_social_default_image

        if res_model not in ('website.page', 'ir.ui.view') and 'seo_name' in record:  # allow custom slugify
            res['seo_name_default'] = slugify(record.display_name)  # default slug, if seo_name become empty
            res['seo_name'] = record.seo_name and slugify(record.seo_name) or ''
        return res

    @http.route(['/google<string(length=16):key>.html'], type='http', auth="public", website=True, sitemap=False)
    def google_console_search(self, key, **kwargs):
        if not request.website.google_search_console:
            logger.warning('Google Search Console not enable')
            raise werkzeug.exceptions.NotFound()

        trusted = request.website.google_search_console.lstrip('google').rstrip('.html')
        if key != trusted:
            if key.startswith(trusted):
                request.website.sudo().google_search_console = "google%s.html" % key
            else:
                logger.warning('Google Search Console %s not recognize' % key)
                raise werkzeug.exceptions.NotFound()

        return request.make_response("google-site-verification: %s" % request.website.google_search_console)

    @http.route('/website/google_maps_api_key', type='json', auth='public', website=True)
    def google_maps_api_key(self):
        return json.dumps({
            'google_maps_api_key': request.website.google_maps_api_key or ''
        })

    # ------------------------------------------------------
    # Themes
    # ------------------------------------------------------

    def _get_customize_views(self, xml_ids):
        View = request.env["ir.ui.view"].with_context(active_test=False)
        if not xml_ids:
            return View
        domain = [("key", "in", xml_ids)] + request.website.website_domain()
        return View.search(domain).filter_duplicate()

    @http.route(['/website/theme_customize_get'], type='json', auth='user', website=True)
    def theme_customize_get(self, xml_ids):
        views = self._get_customize_views(xml_ids)
        return views.filtered('active').mapped('key')

    @http.route(['/website/theme_customize'], type='json', auth='user', website=True)
    def theme_customize(self, enable=None, disable=None):
        """
        Enables and/or disables views according to list of keys.

        :param enable: list of views' keys to enable
        :param disable: list of views' keys to disable
        """
        self._get_customize_views(disable).filtered('active').write({'active': False})
        self._get_customize_views(enable).filtered(lambda x: not x.active).write({'active': True})

    @http.route(['/website/theme_customize_bundle_reload'], type='json', auth='user', website=True)
    def theme_customize_bundle_reload(self):
        """
        Reloads asset bundles and returns their unique URLs.
        """
        context = dict(request.context)
        return {
            'web.assets_common': request.env['ir.qweb']._get_asset_link_urls('web.assets_common', options=context),
            'web.assets_frontend': request.env['ir.qweb']._get_asset_link_urls('web.assets_frontend', options=context),
            'website.assets_editor': request.env['ir.qweb']._get_asset_link_urls('website.assets_editor', options=context),
        }

    @http.route(['/website/make_scss_custo'], type='json', auth='user', website=True)
    def make_scss_custo(self, url, values):
        """
        Params:
            url (str):
                the URL of the scss file to customize (supposed to be a variable
                file which will appear in the assets_common bundle)

            values (dict):
                key,value mapping to integrate in the file's map (containing the
                word hook). If a key is already in the file's map, its value is
                overridden.

        Returns:
            boolean
        """
        request.env['web_editor.assets'].make_scss_customization(url, values)
        return True

    # ------------------------------------------------------
    # Server actions
    # ------------------------------------------------------

    @http.route([
        '/website/action/<path_or_xml_id_or_id>',
        '/website/action/<path_or_xml_id_or_id>/<path:path>',
    ], type='http', auth="public", website=True)
    def actions_server(self, path_or_xml_id_or_id, **post):
        ServerActions = request.env['ir.actions.server']
        action = action_id = None

        # find the action_id: either an xml_id, the path, or an ID
        if isinstance(path_or_xml_id_or_id, str) and '.' in path_or_xml_id_or_id:
            action = request.env.ref(path_or_xml_id_or_id, raise_if_not_found=False).sudo()
        if not action:
            action = ServerActions.sudo().search(
                [('website_path', '=', path_or_xml_id_or_id), ('website_published', '=', True)], limit=1)
        if not action:
            try:
                action_id = int(path_or_xml_id_or_id)
                action = ServerActions.sudo().browse(action_id).exists()
            except ValueError:
                pass

        # run it, return only if we got a Response object
        if action:
            if action.state == 'code' and action.website_published:
                # use main session env for execution
                action_res = ServerActions.browse(action.id).run()
                if isinstance(action_res, werkzeug.wrappers.Response):
                    return action_res

        return request.redirect('/')


# ------------------------------------------------------
# Retrocompatibility routes
# ------------------------------------------------------
class WebsiteBinary(http.Controller):

    @http.route([
        '/website/image',
        '/website/image/<xmlid>',
        '/website/image/<xmlid>/<int:width>x<int:height>',
        '/website/image/<xmlid>/<field>',
        '/website/image/<xmlid>/<field>/<int:width>x<int:height>',
        '/website/image/<model>/<id>/<field>',
        '/website/image/<model>/<id>/<field>/<int:width>x<int:height>'
    ], type='http', auth="public", website=False, multilang=False)
    def content_image(self, id=None, max_width=0, max_height=0, **kw):
        if max_width:
            kw['width'] = max_width
        if max_height:
            kw['height'] = max_height
        if id:
            id, _, unique = id.partition('_')
            kw['id'] = int(id)
            if unique:
                kw['unique'] = unique
        return Binary().content_image(**kw)

    # if not icon provided in DOM, browser tries to access /favicon.ico, eg when opening an order pdf
    @http.route(['/favicon.ico'], type='http', auth='public', website=True, multilang=False, sitemap=False)
    def favicon(self, **kw):
        website = request.website
        response = request.redirect(website.image_url(website, 'favicon'), code=301)
        response.headers['Cache-Control'] = 'public, max-age=%s' % http.STATIC_CACHE_LONG
        return response
