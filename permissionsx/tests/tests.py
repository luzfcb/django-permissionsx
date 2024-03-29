"""
PermissionsX - Authorization for Django.

:copyright: Copyright (c) 2013-2014 by Robert Pogorzelski.
:license:   BSD, see LICENSE for more details.

"""
from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.contrib.auth import login

from permissionsx.contrib.django.views import DjangoViewMixin
from permissionsx.models import Arg
from permissionsx.tests.models import TestObject
from permissionsx.tests.permissions import *
from permissionsx.tests.test_utils import SettingsOverride
from permissionsx.tests.test_utils import UtilityTestCase
from permissionsx.tests.views import SimpleGetView


class PermissionsDefinitionsTests(UtilityTestCase):

    def test_is_authenticated(self):
        request = self.get_request_for_user(self.user)
        self.assertFalse(AuthenticatedPermissions().check(request))
        login(request, self.user)
        self.assertTrue(AuthenticatedPermissions().check(request))

    def test_is_superuser(self):
        request = self.get_request_for_user(self.admin)
        self.assertFalse(AuthenticatedPermissions().check(request))
        login(request, self.admin)
        self.assertTrue(AuthenticatedPermissions().check(request))
        self.assertTrue(SuperuserPermissions().check(request))

    def test_is_staff(self):
        request_staff = self.get_request_for_user(self.staff)
        request_admin = self.get_request_for_user(self.admin)
        login(request_staff, self.staff)
        login(request_admin, self.admin)
        self.assertTrue(StaffPermissions().check(request_staff))
        self.assertFalse(StaffPermissions().check(request_admin))

    def test_staff_or_superuser(self):
        request_staff = self.get_request_for_user(self.staff)
        request_admin = self.get_request_for_user(self.admin)
        login(request_staff, self.staff)
        login(request_admin, self.admin)
        self.assertTrue(OrStaffSuperuserPermissions().check(request_staff))
        self.assertTrue(OrStaffSuperuserPermissions().check(request_admin))

    def test_staff_and_superuser(self):
        request_staff = self.get_request_for_user(self.staff)
        request_admin = self.get_request_for_user(self.admin)
        request_user = self.get_request_for_user(self.user)
        login(request_staff, self.staff)
        login(request_admin, self.admin)
        login(request_user, self.user)
        self.assertFalse(AndStaffSuperuserPermissions().check(request_staff))
        self.assertFalse(AndStaffSuperuserPermissions().check(request_admin))
        self.assertFalse(AndStaffSuperuserPermissions().check(request_user))
        self.staff.is_superuser = True
        self.admin.is_staff = True
        self.assertTrue(AndStaffSuperuserPermissions().check(request_staff))
        self.assertTrue(AndStaffSuperuserPermissions().check(request_admin))
        self.assertFalse(AndStaffSuperuserPermissions().check(request_user))

    def test_request_objects(self):
        request_user = self.get_request_for_user(self.user)
        request_admin = self.get_request_for_user(self.admin)
        login(request_user, self.user)
        self.assertFalse(IsPublicPermissions().check(request_user))
        self.assertFalse(IsPublicPermissions().check(request_admin))
        self.assertFalse(AuthenticatedPermissions().check(request_admin))
        self.user.get_profile().is_public = True
        self.assertTrue(IsPublicPermissions().check(request_user))
        self.assertFalse(IsPublicPermissions().check(request_admin))

    def test_negation_request_objects(self):
        request_user = self.get_request_for_user(self.user)
        request_admin = self.get_request_for_user(self.admin)
        login(request_user, self.user)
        login(request_admin, self.admin)
        self.assertTrue(AuthenticatedPermissions().check(request_user))
        self.assertTrue(AuthenticatedPermissions().check(request_admin))
        self.assertFalse(NegatePermissions().check(request_user))
        self.assertFalse(NegatePermissions().check(request_admin))
        self.user.get_profile().is_public = True
        self.admin.get_profile().is_public = True
        self.assertTrue(NegatePermissions().check(request_user))
        self.assertTrue(NegatePermissions().check(request_admin))

    def test_nested_permissions(self):
        request_admin = self.get_request_for_user(self.admin)
        self.assertFalse(NestedPermissions().check(request_admin))
        login(request_admin, self.admin)
        self.assertFalse(NestedPermissions().check(request_admin))
        self.admin.username = 'admin2'
        self.assertFalse(NestedPermissions().check(request_admin))
        self.admin.is_staff = True
        self.assertTrue(NestedPermissions().check(request_admin))

    def test_request_params(self):
        request_admin = self.get_request_for_user(self.admin)
        self.assertFalse(RequestParamPermissions().check(request_admin))
        login(request_admin, self.admin)
        self.assertTrue(RequestParamPermissions().check(request_admin))

    def test_overrides(self):
        request_admin = self.get_request_for_user(self.admin)
        OverrideIfFalsePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_FALSE, request_admin.permissionsx_return_overrides[0]())
        OverrideIfTrueFalsePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_FALSE, request_admin.permissionsx_return_overrides[0]())
        NegatedOverrideIfTrueFalsePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_FALSE, request_admin.permissionsx_return_overrides[0]())
        NestedNegatedOverridePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_FALSE, request_admin.permissionsx_return_overrides[0]())
        login(request_admin, self.admin)
        OverrideIfTruePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_TRUE, request_admin.permissionsx_return_overrides[0]())
        OverrideIfTrueFalsePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_TRUE, request_admin.permissionsx_return_overrides[0]())
        NegatedOverrideIfTrueFalsePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_TRUE, request_admin.permissionsx_return_overrides[0]())
        NestedNegatedOverridePermissions().check(request_admin)
        self.assertEqual(OVERRIDE_TRUE, request_admin.permissionsx_return_overrides[0]())

    def test_oneliners(self):
        request = self.get_request_for_user(self.user)
        self.assertFalse(Permissions(P(user__is_authenticated=True) & P(user__username=request.user.username)).check(request))
        login(request, self.user)
        self.assertTrue(Permissions(P(user__is_authenticated=True) | P(user__username='someotheruser')).check(request))
        Permissions(user_is_authenticated & P(user__is_superuser=True, if_false=if_true_override)).check(request)
        self.assertEqual(OVERRIDE_TRUE, request.permissionsx_return_overrides[0]())
        Permissions(user_is_superuser | P(user__is_staff=True, if_false=if_false_override)).check(request)
        self.assertEqual(OVERRIDE_FALSE, request.permissionsx_return_overrides[0]())
        permissions_tested = Permissions(
            P(user__is_authenticated=True) &
            P(user__is_staff=True, if_false=if_false_override) &
            P(user__is_superuser=False)
        )
        permissions_tested.check(request)
        self.assertEqual(OVERRIDE_FALSE, request.permissionsx_return_overrides[0]())
        login(request, self.staff)
        permissions_tested = Permissions(
            P(user__is_authenticated=True) &
            P(user__is_staff=True, if_true=if_true_override) &
            P(user__is_superuser=False)
        )
        permissions_tested.check(request)
        self.assertEqual(OVERRIDE_TRUE, request.permissionsx_return_overrides[0]())

    def test_request_arguments(self):
        request = self.get_request_for_user(self.user)
        setattr(request, 'user2', self.admin)
        login(request, self.user)
        self.assertTrue(Permissions(P(user__get_profile__is_attached_to_user=Arg('user'))).check(request))
        self.assertFalse(Permissions(P(user__get_profile__is_attached_to_user=Arg('user2'))).check(request))

    def test_nested_negated(self):
        request_admin = self.get_request_for_user(self.admin)
        self.assertFalse(NestedNegatedPermissions().check(request_admin))
        login(request_admin, self.admin)
        self.assertTrue(NestedNegatedPermissions().check(request_admin))

    def test_children(self):
        self.assertEqual(
            '(&(&(~(&{\'user\': 1})),(|{\'user\': 2},(~(&{\'user\': 3})))))',
            str(P(~P(user=1) & P(P(user=2) | ~P(user=3))))
        )


class PermissionsDjangoViews(UtilityTestCase):

    def setUp(self):
        super(PermissionsDjangoViews, self).setUp()
        self.test_object = TestObject.objects.create(title='Test!')

    def test_authenticated(self):
        response = self.client.get(reverse('authenticated'), follow=True)
        self.assertContains(response, 'Login')
        self.login(self.client, 'user')
        response = self.client.get(reverse('authenticated'), follow=True)
        self.assertContains(response, 'Passed')

    def test_get_profile(self):
        # NOTE: Uses OrStaffSuperuserPermissions == P(user__is_staff=True) | P(user__is_administrator=True)
        response = self.client.get(reverse('get_profile'), follow=True)
        self.assertContains(response, 'Login')
        self.login(self.client, 'user')
        self.assertContains(response, 'Login')
        self.login(self.client, 'staff')
        response = self.client.get(reverse('get_profile'), follow=True)
        self.assertContains(response, 'Passed')
        self.login(self.client, 'admin')
        response = self.client.get(reverse('get_profile'), follow=True)
        self.assertContains(response, 'Passed')

    def test_settings_logout(self):
        with SettingsOverride(PERMISSIONSX_LOGOUT_IF_DENIED=True):
            self.login(self.client, 'user')
            response = self.client.get(reverse('authenticated'), follow=True)
            self.assertContains(response, 'Passed')
            self.client.get(reverse('superuser'), follow=True)
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_settings_redirect_url(self):
        with SettingsOverride(PERMISSIONSX_REDIRECT_URL='/accounts/login2/'):
            response = self.client.get(reverse('authenticated'), follow=True)
            self.assertContains(response, 'Login2')

    def test_response_class(self):
        response = self.client.get(reverse('response_class'), follow=True)
        self.assertContains(response, 'Access Denied')
        self.assertContains(response, 'Login')

    def test_if_false_override(self):
        self.login(self.client, 'user')
        response = self.client.get(reverse('overrides_if_false'), follow=True)
        self.assertContains(response, 'Login2')

    def test_if_true_override(self):
        response = self.client.get(reverse('overrides_if_true'), follow=True)
        self.assertContains(response, 'Login')
        self.login(self.client, 'user')
        response = self.client.get(reverse('overrides_if_true'), follow=True)
        self.assertContains(response, 'Passed')
        self.login(self.client, 'admin')
        response = self.client.get(reverse('overrides_if_true'), follow=True)
        self.assertContains(response, 'Welcome')

    def test_both_overrides(self):
        response = self.client.get(reverse('overrides_both'), follow=True)
        self.assertContains(response, 'Login2')
        self.login(self.client, 'user')
        response = self.client.get(reverse('overrides_both'), follow=True)
        self.assertContains(response, 'Passed')
        self.login(self.client, 'admin')
        response = self.client.get(reverse('overrides_both'), follow=True)
        self.assertContains(response, 'Welcome')

    def test_subsequent_overrides(self):
        response = self.client.get(reverse('subsequent_overrides'), follow=True)
        self.assertContains(response, 'Login2')
        self.login(self.client, 'user')
        response = self.client.get(reverse('subsequent_overrides'), follow=True)
        self.assertContains(response, 'Welcome')

    def test_template_tag(self):
        response = self.client.get(reverse('menu'), follow=True)
        self.assertContains(response, 'Login')
        self.login(self.client, 'user')
        response = self.client.get(reverse('menu'), follow=True)
        self.assertContains(response, 'User Menu')
        self.login(self.client, 'staff')
        response = self.client.get(reverse('menu'), follow=True)
        self.assertContains(response, 'Staff Menu')

    def test_combining_permissions(self):

        class SomeBasicObjectPermissions(Permissions):

            rules = P(some_object1__title='Some Object 1')

            def get_rules(self, request, **kwargs):
                request.some_object1 = TestObject(title='Some Object 1')
                request.some_object2 = TestObject(title='Some Object 2')
                request.some_object3 = TestObject(title='Some Object 3')
                return P(some_object2__title='Some Object 2')

        class SomeObjectPermissions(SomeBasicObjectPermissions):

            def get_rules(self, request, **kwargs):
                rules = super(SomeObjectPermissions, self).get_rules(request, **kwargs)
                request.some_object4 = TestObject(title='Some Object 4')
                return rules & P(some_object3__title='Some Object 3')

        class TestView(DjangoViewMixin, SimpleGetView):

            permissions = SomeObjectPermissions(
                P(some_object4__title='Some Object 4')
            )

        request = self.factory.get('/')
        combined_rules = TestView.permissions.get_combined_rules(request)
        self.assertEqual(
            str(combined_rules),
            '(&{\'some_object1__title\': \'Some Object 1\'},{\'some_object4__title\': \'Some Object 4\'},{\'some_object2__title\': \'Some Object 2\'},{\'some_object3__title\': \'Some Object 3\'})'
        )

    def test_combining_permissions_with_none(self):

        class SomeObjectPermissions(Permissions):

            # NOTE: Inherits `permissions == None` from Permissions.
            def get_rules(self, request, **kwargs):
                request.some_object = TestObject(title='Some Object')

        class TestView(DjangoViewMixin, SimpleGetView):

            permissions = SomeObjectPermissions(
                P(user_is_staff | user_is_superuser)
            )

        request = self.factory.get('/')
        response = TestView().dispatch(request)
        self.assertEqual(response.status_code, 200) #pylint: disable-msg=E1103
        self.assertEqual(request.some_object.title, 'Some Object') #pylint: disable-msg=E1103

