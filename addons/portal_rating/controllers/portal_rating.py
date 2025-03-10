from odoo import http, _
from odoo.http import request


class PortalRating(http.Controller):

    @http.route(['/website/rating/comment'], type='json', auth="user", methods=['POST'], website=True)
    def publish_rating_comment(self, rating_id, publisher_comment):
        rating = request.env['rating.rating'].search([('id', '=', int(rating_id))])
        if not rating:
            return {'error': _('Invalid rating')}
        rating.write({'publisher_comment': publisher_comment})
        # return to the front-end the created/updated publisher comment
        return rating.read(['publisher_comment', 'publisher_id', 'publisher_datetime'])[0]
