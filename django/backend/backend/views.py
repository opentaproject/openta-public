import csv
import logging
from io import StringIO
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.template import loader
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.views.generic.edit import CreateView, FormView

from rest_framework.decorators import api_view
from rest_framework.response import Response
from ratelimit.decorators import ratelimit
from ratelimit.mixins import RatelimitMixin

from backend.forms import (
    BatchAddUsersForm,
    EmailUsersForm,
    RegisterWithPasswordForm,
    UserCreateForm,
    UserCreateFormDomain,
    UserCreateFormNoPassword,
)
from backend.forms import CustomPasswordResetForm
from backend.user_utilities import send_activation_mail, send_email_object
from course.models import Course
from course.serializers import CourseSerializer
from exercises.views.file_handling import serve_file

logger = logging.getLogger(__name__)


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


class RegisterUser(CreateView):
    """
    View for registering user where password is supplied at registration
    """

    template_name = 'register.html'
    form_class = UserCreateForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        super().form_valid(form)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _('Registration complete, check inbox for ' 'activation mail (possibly spam folder).'),
        )
        return redirect(reverse('login'))


class RegisterUserNoPassword(CreateView):
    """
    View for user registration where password is given at activation time.
    """

    template_name = 'register.html'
    form_class = UserCreateFormNoPassword
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        super().form_valid(form)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _('Registration complete, check inbox ' 'for activation mail (possibly spam folder).'),
        )
        return redirect(reverse('login'))


class RegisterUserDomain(CreateView):
    """View for user registration by domain.

    Password is given at activation time and the email is locked to specific domains.

    """

    template_name = 'register.html'
    form_class = UserCreateFormDomain
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['domains'] = Course.objects.registration_domains()
        return ctx

    def form_valid(self, form):
        super().form_valid(form)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _('Registration complete, check inbox for ' 'activation mail (possibly spam folder).'),
        )
        return redirect(reverse('login'))


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
    response = {
        'username': request.user.get_username(),
        'user_pk': request.user.pk,
        'admin': request.user.is_staff,
        'groups': groups,
    }
    course = Course.objects.first()
    if course is not None:
        response.update({'course': course.course_name})
        response.update({'course_pk': course.pk})
    else:
        response.update({'course': 'OpenTA'})
        logger.error('No course found')
    return Response(response)


@ratelimit(key='ip', rate='5/30s')
def login(request):
    """Login view.

    Returns:
        Login view unless rate limited in which case rate_limit.html
    """
    course = Course.objects.first()
    course_data = CourseSerializer(course).data
    if course_data['icon'] is not None:
        course_data['icon'] = '/' + settings.SUBPATH + course_data['icon'].lstrip('/')
    extra = {
        'course': course_data,
        'openta_version': settings.VERSION if hasattr(settings, 'VERSION') else "",
    }
    if not getattr(request, 'limited', False) or settings.RUNNING_DEVSERVER:
        return auth_views.login(request, extra_context=extra)
    else:
        return render(request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')})


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
    return auth_views.login(request, 'registration/login.html')


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


@login_required
def main(request):
    """The main frontend view.

    Returns:
        The frontend app in base_main.html if authorized, otherwise login screen.
    """
    course = Course.objects.first()
    course_data = CourseSerializer(course).data
    extra = dict(course=course_data)
    response = render(request, "base_main.html", context=extra)
    if settings.CSRF_COOKIE_NAME:
        response.set_cookie(key='csrf_cookie_name', value=settings.CSRF_COOKIE_NAME)
        subpath = (settings.SUBPATH).strip('/')
        response.set_cookie(key='subpath', value=subpath)
    return response


class RegisterByPassword(RatelimitMixin, FormView):
    template_name = 'registration/register_with_password.html'
    form_class = RegisterWithPasswordForm
    ratelimit_key = 'ip'
    ratelimit_rate = '5/30s'

    def form_valid(self, form):
        if getattr(self.request, 'limited', False):
            return render(
                self.request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')}
            )
        course = Course.objects.first()
        if (
            course.registration_by_password
            and course.registration_password == form.cleaned_data['password']
        ):
            return redirect(
                reverse('register-with-password') + 'register/' + course.registration_password
            )
        return redirect(reverse('register-with-password'))


@ratelimit(key='ip', rate='5/30s')
def validate_and_show_registration(request, password):
    """Register with password.

    Register user with password view that handles the form submission
    of the register with password form.
    """
    if getattr(request, 'limited', False):
        return render(request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')})
    course = Course.objects.first()
    if course.registration_by_password and course.registration_password == password:
        return RegisterUserNoPassword.as_view()(request)


class BatchAddUserView(PermissionRequiredMixin, FormView):
    """Add many users from a CSV file.
    
    With a CSV file with format:
        "First name" "Last name" "E-mail address" "Username"
        "..." "..." "..." "..."
        ...

    Returns:
        A view with 3 steps: a CSV file upload that then gets parsed and shown before a
        confirmation of add is asked and then finally adds users.
    """

    permission_required = "auth.add_user"
    template_name = 'batch_add_users.html'
    form_class = BatchAddUsersForm

    def form_valid(self, form):
        if 'batch_file' in form.cleaned_data and form.cleaned_data['batch_file'] is not None:
            raw = form.cleaned_data['batch_file'].read()
            uni = raw.decode('latin-1')
            dialect = csv.Sniffer().sniff(uni)
            data = list(csv.reader(StringIO(uni), dialect=dialect))
            labels = data[0]
            users = []
            for row in data[1:]:
                parsed_row = [
                    {label.replace(' ', '_').replace('-', '_'): value}
                    for label, value in zip(labels, row)
                ]
                res = {}
                for item in parsed_row:
                    tmp = {}
                    tmp.update(res)
                    tmp.update(item)
                    res = tmp

                users.append(res)
            self.request.session['users'] = users
            return render(self.request, 'batch_add_users.html', {'form': form, 'users': users})
        if 'adduser' in self.request.POST:
            for user in self.request.session['users']:
                dbuser, created = User.objects.get_or_create(
                    username=user['Username'],
                    defaults={
                        'email': user['E_mail_address'],
                        'first_name': user['First_name'],
                        'last_name': user['Last_name'],
                    },
                )
                dbuser.is_active = False
                dbuser.save()

                if created:
                    messages.add_message(
                        self.request, messages.SUCCESS, "Added user " + user['Username']
                    )
                else:
                    messages.add_message(
                        self.request,
                        messages.WARNING,
                        ("User " + user['Username'] + " already added!"),
                    )
                try:
                    activation_url = send_activation_mail(
                        user['Username'], user['E_mail_address'], 'user-activation-and-reset'
                    )
                    logger.info(
                        "Activation mail sent for "
                        + user['Username']
                        + ' with activation link '
                        + activation_url
                    )
                    messages.add_message(
                        self.request,
                        messages.SUCCESS,
                        "Activation mail sent for " + user['Username'],
                    )
                except SMTPException:
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        "Activation mail send error for " + user['Username'],
                    )

        return render(self.request, 'batch_add_users.html', {'form': form})


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
    from_email = Course.objects.course_email()
    template_name = 'registration/password_reset_subject.txt'
    subject = loader.render_to_string(template_name)
    if getattr(request, 'limited', False):
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


def email_users(request, context):
    """Email multiple users.
    
    Args:
        request: request
        context: extra context
    
    Returns:
        HttpResponse: Email template response
    """

    if request.POST.get('post-send-emails'):
        form = EmailUsersForm(request.POST)
        if form.is_valid():
            users = User.objects.filter(pk__in=request.session['email_users'])
            addresses = users.values_list('email', flat=True)
            email = EmailMessage(
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['message'],
                from_email=Course.objects.course_name().lower() + "@openta.se",
                to=addresses,
            )
            send_email_object(email)
            messages.info(request, "Emailed " + str(users.count()) + " students")
    else:
        form = EmailUsersForm()
        users = User.objects.filter(pk__in=request.session['email_users'])
        context.update(
            {
                'form': form,
                'users': users,
                'show_users': request.user.has_perm('exercises.show_student_id'),
            }
        )
        return TemplateResponse(request, 'email_users.html', context)


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
