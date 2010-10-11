from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client


from ganeti.models import Profile


__all__ = ('TestProfileModel', 'TestAccountViews',)


class TestProfileModel(TestCase):
    
    def setUp(self):
        self.tearDown()
    
    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()
    
    def test_trivial(self):
        """ Tests that object can be created """
        Profile()
    
    def test_signal_listeners(self):
        """
        Test automatic creation and deletion of profile objects
        """
        user = User(username='tester')
        user.save()
        
        # profile created
        profile = user.get_profile()
        self.assert_(profile, 'profile was not created')
        
        # profile deleted
        user.delete()
        self.assertFalse(Profile.objects.filter(id=profile.id).exists())


class TestAccountViews(TestCase):
    
    def setUp(self):
        self.tearDown()
        
        user = User(username='tester', email='test@test.com')
        user.set_password('secret')
        user.save()
        
        client = Client()
        
        g = globals()
        g['user'] = user
        g['c'] = client
    
    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()
    
    def test_view_login(self):
        """
        Test logging in
        """
        url = '/accounts/login/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # no username
        data = {'password':'secret'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'login.html')
        
        # no password
        data = {'username':'tester'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'login.html')
        
        # bad username
        data = {'username':'invalid', 'password':'secret'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'login.html')
        
        # bad password
        data = {'username':'tester', 'password':'incorrect'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'login.html')
        
        # user with perms on no virtual machines
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'login.html')
        
        # invalid method
        data = {'username':'tester', 'password':'secret'}
        response = c.get(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'index.html')
        
        # success
        data = {'username':'tester', 'password':'secret'}
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'index.html')
    
    def test_view_logout(self):
        """
        Test logging out
        """
        url = '/accounts/logout/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # successful logout
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'login.html')
    
    def test_view_profile(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # get form
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_profile.html')
        
        # bad method (CSRF check)
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'foo'}
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('test@test.com', user.email)
        self.assert_(c.login(username=user.username, password='secret'))
        
        # bad old password
        data = {'email':'new@test.com', 'old_password':'incorrect','new_password':'foo', 'confirm_password':'foo'}
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('test@test.com', user.email)
        self.assert_(c.login(username=user.username, password='secret'))
        
        # not confirmed
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'incorrect'}
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('test@test.com', user.email)
        self.assert_(c.login(username=user.username, password='secret'))
        
        # change email
        data = {'email':'new@test.com'}
        response = c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('new@test.com', user.email)
        
        # change password
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'foo'}
        response = c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('new@test.com', user.email)
        self.assert_(c.login(username=user.username, password='foo'))
