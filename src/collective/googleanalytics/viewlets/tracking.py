import sys
from urllib import urlencode
from zope.component import queryMultiAdapter
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.analytics.view import AnalyticsViewlet
from collective.googleanalytics.interfaces.tracking import IAnalyticsTrackingPlugin

User_PII_PluginName = "User PII"

class AnalyticsTrackingViewlet(AnalyticsViewlet):
    """
    A viewlet that inserts the Google Analytics tracking code
    at the end of the page. We override the default Plone viewlet
    so that we can exclude the code for certain roles.
    """

    index = ViewPageTemplateFile('tracking.pt')

    def render(self):
        return self.index()

    def __init__(self, context, request, view, manager):
        super(AnalyticsTrackingViewlet, self).__init__(context, request, view, manager)
        self.analytics_tool = getToolByName(context, "portal_analytics")
        self.membership_tool = getToolByName(context, "portal_membership")

    def available(self):
        """
        Checks to see whether the viewlet should be rendered based on the role
        of the user and the selections for excluded roles in the configlet.
        """

        member = self.membership_tool.getAuthenticatedMember()

        for role in self.analytics_tool.tracking_excluded_roles:
            if member.has_role(role):
                return False
        return True

    def getTrackingWebProperty(self):
        """
        Returns the Google web property ID for the selected tracking profile,
        or an empty string if no tracking profile is selected.
        """
        return self.analytics_tool.__dict__.get('tracking_web_property', None)

    def is_tracking_custom(self):
        return (self.analytics_tool.__dict__.get('tracking_web_property', None)
                == '_TRACKING_CODE_CUSTOM')

    def get_tracking_custom(self):
        """
        Returns True custom tracking code to connect with google.
        """
        return self.analytics_tool.__dict__.get('custom_js', '')

    def renderUserPPI(self):
        plugin = queryMultiAdapter(
                (self.context, self.request),
                interface=IAnalyticsTrackingPlugin,
                name=User_PII_PluginName,
                default=None,
            )
        if plugin:
            return plugin()

    def renderPlugins(self):
        """
        Render each of the selected tracking plugins for the current context
        and request.
        """

        results = []
        pnames = [a for a in self.analytics_tool.tracking_plugin_names 
                                            if a != User_PII_PluginName]
        for plugin_name in pnames:
            plugin = queryMultiAdapter(
                (self.context, self.request),
                interface=IAnalyticsTrackingPlugin,
                name=plugin_name,
                default=None,
            )
            if plugin:
                results.append(plugin())
        return '\n'.join(results)

    def getsearchcat(self):
        return self.view.__name__

    def renderPageview(self):
        push_params = ["'send'", "'pageview'"]
        if self.view.__name__.startswith("search"):
            query = {'q': self.request.get('SearchableText', ''),
                     'searchcat': self.getsearchcat()}
            push_params.append("'/searchresult?%s'" % urlencode(query))
        return "ga(%s);" % ', '.join(push_params)

