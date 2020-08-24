import logging
from django.contrib.auth.views import LoginView
from django.utils import translation
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_deny

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.template import loader
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth import logout as syslogout
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie


from rest_framework.decorators import api_view
from rest_framework.response import Response
from ratelimit.decorators import ratelimit
from ratelimit.mixins import RatelimitMixin
from users.models import OpenTAUser

from backend.forms import (
    EmailUsersForm,
    RegisterWithPasswordForm,
    UserCreateFormDomain,
    UserCreateFormNoPassword,
)
from backend.forms import CustomPasswordResetForm
from backend.user_utilities import send_activation_mail, send_email_object
from backend.constants import DONT_REPLY_EMAIL
from course.models import Course
from course.serializers import CourseSerializer
from exercises.views.file_handling import serve_file
from exercises.modelhelpers import enrollment
from hijack.signals import hijack_started, hijack_ended

logger = logging.getLogger(__name__)


def print_hijack_started(sender, hijacker_id, hijacked_id, request, **kwargs):
    request.session['hijacked'] = True
    print('%d has hijacked %d' % (hijacker_id, hijacked_id))


hijack_started.connect(print_hijack_started)


def print_hijack_ended(sender, hijacker_id, hijacked_id, request, **kwargs):
    request.session['hijacked'] = False
    print('%d has released %d' % (hijacker_id, hijacked_id))


hijack_ended.connect(print_hijack_ended)


class ActivateAndReset(FormView):
    """
    View for user activation and password reset. Adds user to group Student.
    """

    template_name = 'registration/set_password.html'
    success_url = reverse_lazy('login')

    def get_form(self):
        user = self.kwargs.get('user', None)
        return SetPasswordForm(user, **self.get_form_kwargs())

    def form_valid(self, form):
        super().form_valid(form)
        form.save()
        try:
            group = Group.objects.get(name='Student')
            group.user_set.add(self.kwargs['user'])
        except ObjectDoesNotExist:
            pass
        self.kwargs['user'].is_active = True
        self.kwargs['user'].save()
        logger.info("Added and activated user " + str(self.kwargs['user']))
        messages.add_message(
            self.request, messages.SUCCESS, _('Password is now set, please login.')
        )
        return redirect(reverse('login'))


class RegisterUserNoPassword(CreateView):
    """
    View for user registration where password is given at activation time.
    """

    template_name = 'register.html'
    form_class = UserCreateFormNoPassword
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        ctx['course'] = CourseSerializer(course).data
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        super().form_valid(form)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _('Registration complete, check inbox ' 'for activation mail (possibly spam folder).'),
        )
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        return redirect(reverse('login') + course.course_name)


class RegisterUserDomain(CreateView):
    """View for user registration by domain.

    Password is given at activation time and the email is locked to specific domains.

    """

    template_name = 'register.html'
    form_class = UserCreateFormDomain
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        ctx['domains'] = course.get_registration_domains()
        ctx['course'] = CourseSerializer(course).data
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        super().form_valid(form)
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        return redirect(reverse('login', kwargs=dict(course_name=course.course_name)))


@api_view(['GET'])
def login_status(request):
    """Get login information for current user.

    Returns:
        JSON {
            username: (string)
            admin: (bool)
            groups: [string]
            }
    """
    groups = []
    dbgroups = request.user.groups.all()
    for group in dbgroups:
        groups.append(group.name)
    if request.user.is_superuser:
        groups.append('SuperUser')
    lti_login = request.session.get('lti_login', False)
    nonlti_login = request.session.get('nonlti_login', False)
    compactview = request.session.get('compactview', request.session.get('lti_login', False))
    response = {
        'username': request.user.get_username(),
        'user_pk': request.user.pk,
        'admin': request.user.is_staff,
        'groups': groups,
        'lti_login': lti_login,
        'compactview': compactview,
    }
    return Response(response)


@ratelimit(key='ip', rate='5/30s')
def login(request, course_name=None):
    """Login view.

    Returns:
        Login view unless rate limited in which case rate_limit.html
    """
    # get last course name to make it easy to return
    if course_name == None:
        course_name = request.COOKIES.get('last_course_name', None)
    course = None
    try:
        #  IF WE DISALLOW COURSE WITH SAME NAME ON CREATION, WE CAN REVERT THIS LINE
        course = Course.objects.get(course_name__iexact=course_name)
    except Course.DoesNotExist:
        course = Course.objects.order_by('-published', '-pk')[0]
    except Course.MultipleObjectsReturned:
        course = (
            Course.objects.filter(course_name__iexact=course_name)
            .order_by('-published', '-pk')
            .last()
        )

    course_data = CourseSerializer(course).data

    if request.user.is_authenticated:
        return main(request, course_pk=course.pk)

    set_persistent_lang(course, request)

    if course_data['icon'] is not None:
        course_data['icon'] = '/' + settings.SUBPATH + course_data['icon'].lstrip('/')

    extra = {
        'course': course_data,
        'openta_version': settings.VERSION,
        'subpath': '/' + settings.SUBPATH,
        'course_name': course.course_name,
    }
    if not getattr(request, 'limited', False) or settings.RUNNING_DEVSERVER:
        context = { 'extra_context': extra }
        return LoginView.as_view(**context)(request)
    else:
        return render(
            request, 'login rate_limit.html', context={'rate': _('5 times per 30 seconds')}
        )


def activate(request, username, token):
    """User activation where the password was supplied at registration time.

    Returns:
        Login view if successful, otherwise activation_failed.html.
    """
    try:
        key = '%s:%s' % (username, token)
        TimestampSigner().unsign(key, max_age=60 * 60 * 24 * 10)  # Valid for 2 days
        user = User.objects.get(username=username)
        user.is_active = True
        user.save()
    except (BadSignature, SignatureExpired):
        return render(request, "activation_failed.html")
    messages.add_message(request, messages.SUCCESS, _('Activation successful, please login.'))
    return LoginView.as_view()(request)


def set_persistent_lang(course, request):
    course_languages = course.get_languages()
    if course_languages is None:
        lang = 'en'
    else:
        lang = request.COOKIES.get('lang', course_languages[0])

    translation.activate(lang)  # SEE https://docs.djangoproject.com/en/2.1/topics/i18n/translation/
    request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return lang


# def set_persistent_lang(course, request):
#    course_languages = course.get_languages()
#    if course_languages is None:
#        lang = 'en'
#    else:
#        lang = request.COOKIES.get('lang', course_languages[0])
#
#    translation.activate(lang)  # SEE https://docs.djangoproject.com/en/2.1/topics/i18n/translation/
#    request.session[translation.LANGUAGE_SESSION_KEY] = lang
#    return lang


def activate_and_reset(request, username, token):
    """User activation with a form for choosing a password.

    Returns:
        Password form if successful, otherwise activation_failed.html.
    """
    try:
        key = '%s:%s' % (username, token)
        TimestampSigner().unsign(key, max_age=60 * 60 * 24 * 10)  # Valid for 2 days
    except (BadSignature, SignatureExpired):
        return render(request, "activation_failed.html")
    user = User.objects.get(username=username)
    if user.is_active:
        messages.add_message(request, messages.WARNING, _("User is already activated"))
        return render(request, "activation_failed.html")

    return ActivateAndReset.as_view()(request, user=user)


@xframe_options_exempt  # NECESSARY TO KEEP FROM CRASHING IN CANVAS FRAME
@login_required
def view_toggle(request, course_pk=None):
    logging.debug("VIEW TOGGLE")
    request.session['compactview'] = not request.session.get(
        'compactview', request.session.get('lti_login', False)
    )
    return main(request, course_pk)


@xframe_options_exempt  # KEEPS FROM CRASHING FOR PASSWSORD CHANGE
@ensure_csrf_cookie
@login_required
def main(request, course_pk=None):
    """The main frontend view.

    Returns:
        The frontend app in base_main.html if authorized, otherwise login screen.
    """
    if course_pk is None:
        course_pk = request.session.get('course_pk')

    if course_pk is not None:
        course = Course.objects.get(pk=course_pk)
    else:
        if Course.objects.count() == 0:
            messages.add_message(request, messages.WARNING, _("No courses yet"))
            return redirect(reverse('login'))
        course = Course.objects.order_by('-published', '-pk')[0]
        course_pk = course.pk
    user = request.user
    # print("IS HIJACKED", request.session.get('hijacked', False))
    enrolled = int(course_pk) in enrollment(user)
    published_and_enrolled = course.published and enrolled
    msg = ''
    if not enrolled:
        msg = "Not enrolled in course"
    if not course.published:
        msg = "Course not published yet"
    if (
        request.user.groups.filter(name='Student').exists()
        and not published_and_enrolled
        and not request.user.username == 'student'
    ):
        try:
            mycourse = (Course.objects.get(pk=enrollment(user)[0])).course_name
            messages.add_message(request, messages.WARNING, _(msg))
            return redirect('/' + settings.SUBPATH + 'logout/' + mycourse + '/')
        except:
            messages.add_message(request, messages.WARNING, _("Not enrolled!"))
            return redirect('/' + settings.SUBPATH + 'logout/' + course.course_name + '/')

    course_data = CourseSerializer(course).data
    help_url = getattr(settings, 'HELP_URL', '')
    extra = dict(
        course=course_data, timezone=settings.TIME_ZONE, subpath=settings.SUBPATH, help_url=help_url
    )
    lang = set_persistent_lang(course, request)
    response = render(request, "base_main.html", context=extra)
    if settings.CSRF_COOKIE_NAME:
        response.set_cookie(key='csrf_cookie_name', value=settings.CSRF_COOKIE_NAME)
    if request.session.get("launch_presentation_return_url", None):
        response.set_cookie(
            key='launch_presentation_return_url',
            value=request.session.get('launch_presentation_return_url', None),
            path='/',
        )

    subpath = settings.SUBPATH.strip('/')
    response.set_cookie(key='cookieTest', value='enabled', path='/')
    response.set_cookie(key='lang', value=lang, path='/')
    return response


class RegisterByPassword(RatelimitMixin, FormView):
    template_name = 'registration/register_with_password.html'
    form_class = RegisterWithPasswordForm
    ratelimit_key = 'ip'
    ratelimit_rate = '5/30s'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        ctx['domains'] = course.get_registration_domains()
        ctx['course'] = CourseSerializer(course).data
        return ctx

    def form_valid(self, form):
        if getattr(self.request, 'limited', False) and (not settings.RUNNING_DEVSERVER):
            return render(
                self.request,
                'register rate_limit.html',
                context={'rate': _('5 times per 30 seconds')},
            )
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        kwargs = {'course_pk': self.kwargs['course_pk']}
        if (
            course.registration_by_password
            and course.registration_password == form.cleaned_data['password']
        ):
            return redirect(
                reverse('register-with-password', kwargs=kwargs)
                + 'register/'
                + course.registration_password
            )
        return redirect(reverse('register-with-password', kwargs=kwargs))


@ratelimit(key='ip', rate='5/30s')
def validate_and_show_registration(request, course_pk, password):
    """Register with password.

    Register user with password view that handles the form submission
    of the register with password form.
    """
    if getattr(request, 'limited', False) and (not settings.RUNNING_DEVSERVER):
        return render(request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')})
    course = Course.objects.get(pk=course_pk)
    if course.registration_by_password and course.registration_password == password:
        return RegisterUserNoPassword.as_view()(request, course_pk=course_pk)
    else:
        return redirect(reverse('register-with-password', kwargs={'course_pk': course_pk}))


def password_reset_done(request):
    """Add sent success message.

    Wrapper view that adds a success message to the login screen indicating
    that a password reset mail was sent.
    """
    messages.add_message(
        request,
        messages.INFO,
        _("Password reset link sent to your email " "(check your spam folder as well)."),
    )
    return redirect(reverse('login'))


@ratelimit(key='ip', rate='5/1h')
def password_reset(request):
    """Password reset view asking for an email."""
    from_email = DONT_REPLY_EMAIL
    template_name = 'registration/password_reset_subject.txt'
    subject = loader.render_to_string(template_name)
    if getattr(request, 'limited', False) and (not settings.RUNNING_DEVSERVER):
        message = (
            "If you are not receiving an reset link by email, check your"
            "spam filter or junk mail. The email was sent from [{from_email}] with the subject [{subject}]"
        )
        message_format = message.format(from_email=from_email, subject=subject)
        return render(
            request,
            'rate_limit.html',
            context=dict(rate="5 " + _('times per hour.'), extra_message=message_format),
        )

    ret = auth_views.password_reset(
        request, from_email=from_email, password_reset_form=CustomPasswordResetForm
    )

    return ret


def password_reset_complete(request):
    """Add success and login message.

    Wrapper view that adds a success message to the login screen after password was reset.
    """
    messages.add_message(request, messages.INFO, _("Password reset successful, please login."))
    return redirect(reverse('login'))


def serve_public_media(request, asset):
    """Serve public media.

    Args:
        request (HttpRequest): request
        asset (str): Asset path

    Raises:
        Http404: If unauthorized

    Returns:
        HttpResponse: Asset response

    """
    if not asset.startswith('public/'):
        raise Http404('Not authorized')

    return serve_file(settings.MEDIA_URL + asset, asset.split('/')[-1])

@xframe_options_exempt
def trigger_error(request ,msg='SENTRY ERROR TRIGGERED' ):
    assert 1 == 0 , msg
    raise Http404("msg")

@xframe_options_exempt  # NECESSARY TO KEEP FROM CRASHING IN CANVAS FRAME
def logout(request, course_name=None, lti_status='no_lti'):
    if lti_status == 'no_lti':
        request.session['nonlti_login'] = False
        request.session.modified = True
        if course_name == None or course_name == '':
            next_url = '/' + settings.SUBPATH
        else:
            next_url = '/' + settings.SUBPATH + course_name + '/'
        response = HttpResponseRedirect(next_url)
        response.set_cookie(key='last_course_name', value=course_name)  # HAVE THIS FOR NEXT LOGIN
        request.session.modified = True
        syslogout(request)  # Always do syslogout if request is from non-lti-window
        return response
    else:
        next_url = request.COOKIES.get(
            'launch_presentation_return_url', None
        )  # GET FROM COOKIE IN C̄ASE SESSION IS DEAD
        response = HttpResponseRedirect(next_url)
        request.session['lti_login'] = False
        response.set_cookie(key='last_course_name', value=course_name)  # HAVE THIS FOR NEXT LOGIN
        request.session.modified = True
        response = HttpResponseRedirect(next_url)
        syslogout(request)  # Always do syslogout if request is from non-lti-window
        return response


@xframe_options_exempt
def csrf_failure(request, reason=""):
    if 'cookie' in reason:
        reason = reason + ' You need to allow cookies for this site.'
    response = render(request, "csrf_failure.html", {'msg': reason})
    # response = HttpResponseRedirect('https://www.google.com')
    return response
